from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from user_blog.models import Post
from user_page.models import Knowledge


class PostAPIAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(username='author')
        cls.reader = User.objects.create_user(username='reader')
        knowledge = Knowledge.objects.create(user=cls.author, name='Test')
        cls.post = Post.objects.create(
            user=cls.author, knowledge_field=knowledge,
            title='Original title', body='Original body',
        )

    def setUp(self):
        self.client = APIClient()

    def test_authenticated_users_cannot_mutate_posts_through_feed_or_likes(self):
        for user in (self.author, self.reader):
            self.client.force_authenticate(user=user)
            for prefix in ('general_page_api', 'like_api'):
                collection = '/{}/v1/posts/'.format(prefix)
                detail = '{}{}/'.format(collection, self.post.pk)
                for method, url in (
                    ('post', collection), ('put', detail),
                    ('patch', detail), ('delete', detail),
                ):
                    with self.subTest(user=user.username, prefix=prefix, method=method):
                        response = getattr(self.client, method)(
                            url, {'title': 'Changed', 'body': 'Changed'}, format='json',
                        )
                        self.assertEqual(response.status_code, 405)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Original title')
        self.assertEqual(self.post.body, 'Original body')
        self.assertEqual(Post.objects.count(), 1)

    def test_anonymous_users_can_read_but_cannot_write(self):
        for prefix in ('general_page_api', 'like_api'):
            collection = '/{}/v1/posts/'.format(prefix)
            detail = '{}{}/'.format(collection, self.post.pk)
            self.assertEqual(self.client.get(collection).status_code, 200)
            self.assertEqual(self.client.get(detail).status_code, 200)
            for method, url in (
                ('post', collection), ('put', detail),
                ('patch', detail), ('delete', detail),
            ):
                with self.subTest(prefix=prefix, method=method):
                    self.assertEqual(getattr(self.client, method)(url).status_code, 403)
        for action in ('like', 'unlike'):
            self.assertEqual(self.client.post(
                '/like_api/v1/posts/{}/{}/'.format(self.post.pk, action),
            ).status_code, 403)
        self.assertEqual(self.post.likes.count(), 0)

    def test_readers_can_like_and_only_remove_their_own_like(self):
        detail = '/like_api/v1/posts/{}/'.format(self.post.pk)
        for user in (self.author, self.reader):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.post(detail + 'like/').status_code, 200)
        self.assertEqual(self.client.post(detail + 'like/').status_code, 200)
        self.assertEqual(self.post.likes.count(), 2)
        self.assertEqual(self.client.post(detail + 'unlike/').status_code, 200)
        self.assertEqual(list(self.post.likes.values_list('user_id', flat=True)),
                         [self.author.pk])
        self.client.force_authenticate(user=None)
        response = self.client.get(detail + 'fans/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{'username': 'author'}])
