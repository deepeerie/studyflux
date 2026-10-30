from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from user_blog.models import Post
from user_page.models import Knowledge
from user_topics.models import Topic


class TopicFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(username='topic-author')
        cls.stream = Knowledge.objects.create(user=cls.author, name='Main')
        cls.other = Knowledge.objects.create(user=cls.author, name='Other')
        cls.topic = Topic.objects.create(user=cls.author, knowledge=cls.stream, title='Русская тема')
        cls.other_topic = Topic.objects.create(user=cls.author, knowledge=cls.other, title='Русская тема')
        for i in range(17):
            post = Post.objects.create(user=cls.author, knowledge_field=cls.stream, title=str(i))
            post.categories.add(cls.topic.category)
        cls.uncategorized = Post.objects.create(user=cls.author, knowledge_field=cls.stream, title='No topic')
        cls.cross_stream = Post.objects.create(user=cls.author, knowledge_field=cls.other, title='Other stream')
        cls.cross_stream.categories.add(cls.topic.category)
        cls.url = reverse('project_index', args=[cls.author.username, cls.stream.name])

    def test_cyrillic_topic_filter_and_pagination(self):
        response = self.client.get(self.url, {'topic': self.topic.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Русская тема')
        self.assertContains(response, '?topic={}'.format(self.topic.pk))
        self.assertEqual(response.context['paginator'].count, 18)
        self.assertContains(response, '?page=2&amp;topic={}'.format(self.topic.pk))
        second = self.client.get(self.url, {'topic': self.topic.pk, 'page': 2})
        self.assertEqual(len(second.context['posts']), 2)
        self.assertNotIn(self.uncategorized, response.context['posts'])

    def test_all_includes_uncategorized_and_cross_stream_posts(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['paginator'].count, 19)
        self.assertIsNone(response.context['selected_topic'])

    def test_invalid_or_other_stream_topic_is_not_selected(self):
        for value in ('bad', '99999999', str(self.other_topic.pk)):
            with self.subTest(topic=value):
                self.assertEqual(self.client.get(self.url, {'topic': value}).status_code, 404)
