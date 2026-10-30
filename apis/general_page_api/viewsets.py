from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from apis.general_page_api.serializers import PostSerializer
from user_blog.models import Post


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = PageNumberPagination
    queryset = Post.objects.all().order_by('-created_on')
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
