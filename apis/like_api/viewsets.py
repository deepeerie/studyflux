from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from user_blog.models import Post
from .serializers import PostSerializer
from .mixins import LikedMixin


class PostViewSet(LikedMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
