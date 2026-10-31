import io
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from general_page.models import Confirm
from user_blog.models import Comment, Post
from user_page.models import Knowledge
from user_topics.models import Topic
import user_topics.servisec


@override_settings(DEBUG=True)
class LocalDemoTests(TestCase):
    def test_seed_is_idempotent_and_does_not_reset_password_or_content(self):
        with tempfile.TemporaryDirectory() as temp, override_settings(MEDIA_ROOT=temp), patch.dict(os.environ, {'STUDYFLUX_RUNTIME': temp}):
            call_command('seed_demo', stdout=io.StringIO())
            self.assertEqual(User.objects.count(), 2)
            self.assertEqual(Post.objects.count(), 6)
            self.assertEqual(Comment.objects.count(), 4)
            self.assertFalse(User.objects.filter(is_staff=True).exists())
            credentials = json.loads((Path(temp) / 'demo-credentials.json').read_text())
            author = User.objects.get(username='demo')
            self.assertTrue(author.check_password(credentials['password']))
            author.set_password('a new password'); author.save()
            post = Post.objects.first(); post.title = 'My edit'; post.save()
            call_command('seed_demo', stdout=io.StringIO())
            author.refresh_from_db(); post.refresh_from_db()
            self.assertTrue(author.check_password('a new password'))
            self.assertEqual(post.title, 'My edit')
            self.assertEqual(Post.objects.count(), 6)
            self.assertEqual(len(list((Path(temp) / 'demo/covers').glob('*.png'))), 6)

    def test_seed_does_not_touch_existing_non_demo_database(self):
        User.objects.create_user('existing')
        call_command('seed_demo', stdout=io.StringIO())
        self.assertEqual(list(User.objects.values_list('username', flat=True)), ['existing'])
        self.assertEqual(Post.objects.count(), 0)


class ProductJourneyTests(TestCase):
    def setUp(self):
        from django.test import Client
        self.client = Client(enforce_csrf_checks=True)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.temp.name, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.client.get('/')

    def post(self, url, data):
        return self.client.post(url, data, HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)

    def image(self):
        data = io.BytesIO()
        Image.new('RGB', (100, 80), 'navy').save(data, 'PNG')
        return SimpleUploadedFile('cover.png', data.getvalue(), content_type='image/png')

    def test_registration_content_upload_comments_and_reactions(self):
        user = {'username': 'new-reader', 'email': 'new@example.invalid', 'password': 'Local+A&strong-password'}
        response = self.post('/register123/', {'user': json.dumps(user)})
        self.assertFalse(response.json()['error'])
        self.assertEqual(len(mail.outbox), 1)
        confirm = Confirm.objects.get(user__username=user['username'])
        response = self.post('/register123/', {'user': json.dumps(user), 'confirm_code': confirm.code})
        self.assertFalse(response.json()['error'])
        author = User.objects.get(username=user['username'])
        stream = Knowledge.objects.get(user=author)
        response = self.post(reverse('project_creator', args=[author.username, stream.name]),
                             {'title': 'Заметки', 'knowledge': stream.pk, 'description': 'New topic'})
        self.assertEqual(response.status_code, 302)
        topic = Topic.objects.get(user=author)
        create = reverse('article_creation', args=[author.username])
        self.assertContains(self.client.get(create), 'ckeditor')
        payload = {'title': 'First article', 'knowledge_field': stream.pk, 'categories': [topic.category.pk],
                   'header': 'A useful introduction', 'body': '<p>My first article</p>', 'pinned': 'on'}
        response = self.post(create, dict(payload, image=self.image()))
        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(user=author)
        self.assertTrue(Path(post.image.path).is_file())
        payload['title'] = 'Edited article'
        response = self.post(reverse('update_article', args=[author.username, post.pk]), payload)
        self.assertEqual(response.status_code, 302)
        post.refresh_from_db(); self.assertEqual(post.title, 'Edited article')
        response = self.post('/upload/', {'upload': self.image()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['uploaded'], '1')
        comment_url = reverse('add_comment', args=[author.username, post.pk])
        self.assertEqual(self.post(comment_url, {'body': '<script>bad()</script>'}).status_code, 302)
        root = Comment.objects.get(post=post)
        self.assertEqual(root.path, [root.pk])
        self.assertEqual(self.post(comment_url, {'body': 'Reply', 'parent': root.pk}).status_code, 302)
        reply = Comment.objects.exclude(pk=root.pk).get()
        self.assertEqual(reply.path, [root.pk, reply.pk])
        detail = self.client.get(reverse('article_detail', args=[author.username, post.pk]))
        self.assertContains(detail, '&lt;script&gt;bad()&lt;/script&gt;')
        other = Post.objects.create(user=author, knowledge_field=stream, title='Other')
        other_comment = Comment.objects.create(user=author, post=other, body='Separate thread', path=[])
        self.assertEqual(self.post(comment_url, {'body': 'Wrong parent', 'parent': other_comment.pk}).status_code, 404)
        for action, count in [('like', 1), ('unlike', 0)]:
            self.assertEqual(self.post('/like_api/v1/posts/{}/{}/'.format(post.pk, action), {}).status_code, 200)
            self.assertEqual(post.likes.count(), count)
        for i in range(8):
            Post.objects.create(user=author, knowledge_field=stream, title='Extra {}'.format(i), pinned=True)
        self.assertEqual(self.client.get(reverse('article_index', args=[author.username]) + '?page=2').status_code, 200)
        self.assertEqual(self.client.get(reverse('UserPage', args=[author.username]) + '?page=2').status_code, 200)
        feed = self.client.get('/general_page_api/v1/posts/').json()
        item = next(p for p in feed['results'] if p['id'] == post.pk)
        self.assertEqual(self.client.get(item['topics'][0]['url']).status_code, 200)
        self.assertEqual(self.post('/logout_api/', {}).status_code, 200)
        response = self.post('/login/', {'user': json.dumps({'login': user['username'], 'password': user['password']})})
        self.assertFalse(response.json()['error'])
