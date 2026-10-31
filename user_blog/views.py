from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView, DetailView
from user_blog.forms import CommentForm
from user_blog.mixins import ModelFormPostMixin
from user_blog.models import Post, Comment
from django.contrib.auth.mixins import LoginRequiredMixin


class TopicArticles(ListView):
    template_name = 'article_category.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return list(dict.fromkeys(
            Post.objects.filter(user__username=self.kwargs.get('username')) \
                .filter(categories__name=self.kwargs.get('topic')).order_by('-created_on'))
        )  # __contains distinct

    def get_context_data(self, **kwargs):
        context = super(TopicArticles, self).get_context_data(**kwargs)
        context['username'] = self.kwargs.get('username')
        context['topic'] = self.kwargs.get('topic')
        context['knowledge'] = self.kwargs.get('knowledge')
        return context


class CreateArticleView(ModelFormPostMixin, CreateView, LoginRequiredMixin):
    model = Post
    template_name = 'articles_redactor.html'

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        # A form based on the model(post) and does not exist field.user  in the form from request POST, bc commit=False.
        post = form.save(commit=False)
        post.user = self.request.user
        self.object = post
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(CreateArticleView, self).get_context_data(**kwargs)
        context['username'] = 'You'
        return context


class UpdateArticleView(ModelFormPostMixin, UpdateView, LoginRequiredMixin):
    """ View initializes data from the model-object instance """
    model = Post
    template_name = 'articles_redactor.html'

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        # A form based on the model(post) and does not exist field.user  in the form from request POST, bc commit=False.
        post = form.save(commit=False)
        if post.user == self.request.user:
            self.object = post
            return super().form_valid(form)
        else:
            context = self.get_context_data(**self.kwargs)
            context['fail_rights_article'] = True
            return render(self.request, 'articles_redactor.html', context)


class DeleteArticleView(ModelFormPostMixin, DeleteView, LoginRequiredMixin):
    model = Post
    template_name = 'article_confirm_delete.html'

    def get_queryset(self):
        return Post.objects.filter(user__username=self.request.user)


class ListArticles(ListView):
    template_name = 'article_index.html'
    context_object_name = 'post_list'
    paginate_by = 6

    def get_queryset(self):
        return Post.objects.filter(user__username=self.kwargs.get('username')).order_by('-created_on')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.kwargs.get('username')
        return context


class DetailArticleView(DetailView):
    model = Post
    template_name = 'article_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.kwargs.get('username')
        context['comments'] = Comment.objects.filter(post=self.object).order_by('path')

        if self.request.user.is_authenticated:
            context['form'] = CommentForm

        return context

    @method_decorator(login_required)
    def post(self, *qrgs, **kwargs):
        form = CommentForm(self.request.POST)
        post = get_object_or_404(Post, id=self.kwargs.get('post'))

        if form.is_valid():
            parent_id = form.cleaned_data.get('parent')
            parent = get_object_or_404(Comment, id=parent_id, post=post) if parent_id else None
            comment = Comment.objects.create(
                path=[], post=post, user=auth.get_user(self.request),
                body=form.cleaned_data['body'],
            )
            comment.path = (parent.path if parent else []) + [comment.pk]
            comment.save()

        return redirect('article_detail', username=self.kwargs.get('username'), pk=post.pk)
