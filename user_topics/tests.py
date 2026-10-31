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
        cls.topics = [Topic.objects.create(user=cls.author, knowledge=cls.stream, title=title)
                      for title in ('Русская тема', 'Другая тема', 'Same!', 'Same?')]
        for topic in cls.topics:
            post = Post.objects.create(user=cls.author, knowledge_field=cls.stream, title=topic.title)
            post.categories.add(topic.category)
        cls.url = reverse('project_index', args=[cls.author.username, cls.stream.name])

    def test_filter_uses_distinct_ids_and_preserves_original_titles(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for topic in self.topics:
            self.assertContains(response, '<label for="topic-{}">{}</label>'.format(topic.pk, topic.title), html=True)
            self.assertContains(response, 'id="topic-{}"'.format(topic.pk), count=2)
            self.assertContains(response, 'div:not(.topic-{})'.format(topic.pk))
            self.assertContains(response, 'class="topic  topic-{} "'.format(topic.pk))
        self.assertContains(response, 'filter: blur(4px);')
        self.assertNotContains(response, 'display: none;')
        self.assertNotContains(response, '?topic=')
        self.assertContains(response, 'id="All" name="r1" checked')
        self.assertEqual(len(response.context['posts']), 4)

    def test_stale_topic_url_does_not_filter_server_side(self):
        response = self.client.get(self.url, {'topic': self.topics[0].pk})
        self.assertEqual(len(response.context['posts']), 4)
