from rest_framework import serializers
from django.urls import reverse
from apis.general_page_api import services
from apis.like_api import services as likes_services
from user_blog.models import Post
from user_topics.models import Topic


class PostSerializer(serializers.ModelSerializer):
    is_fan = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    knowledge_field = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    user_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id',
            'username',
            'title',
            'image',
            'knowledge_field',
            'is_fan',
            'total_likes',
            'topics',
            'header',
            'body',
            'created_on',
            'last_modified',
            'url',
            'user_url'
        )

    def get_topics(self, obj):
        topics = services.get_topics(obj)
        serializer = TopicSerializer(topics, many=True)
        return serializer.data

    def get_knowledge_field(self, obj):
        knowledge = services.get_knowledge_name(obj)
        return knowledge

    def get_is_fan(self, obj) -> bool:
        user = self.context.get('request').user
        return likes_services.is_fan(obj, user)

    def get_url(self, obj) -> str:
        return f'/users/@{obj.user}/blog/post/{obj.pk}/'

    def get_user_url(self, obj) -> str:
        return f'/users/@{obj.user}'

    def get_username(self, obj) -> str:
        return obj.user.username


class TopicSerializer(serializers.ModelSerializer):
    knowledge = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = (
            'id',
            'knowledge',
            'title',
            'description',
            'url',
        )

    def get_knowledge(self, obj):
        knowledge = services.get_knowledge_name(obj)
        return knowledge

    def get_url(self, obj) -> str:
        return reverse('article_category', args=[obj.category.user.username, obj.knowledge.name, obj.title])
