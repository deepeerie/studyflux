from django import forms
from django.views.generic import CreateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from user_page.models import Knowledge
from .servisec import *


class CreateTopic(LoginRequiredMixin, CreateView):
    model, fields = Topic, ['title', 'knowledge', 'description']
    template_name = 'topics_creator.html'
    widgets = {
        'title': forms.Textarea(attrs={'cols': '100', 'rows': '1', 'class': 'form-control'}),
        'image': forms.FileInput(attrs={'type': 'file', 'class': 'form-control-file'}),
        'description': forms.Textarea(attrs={'cols': '1000', 'rows': '10', 'class': 'form-control'})
    }

    def get_form_class(self):
        return forms.modelform_factory(self.model, fields=self.fields, widgets=self.widgets)

    def get_form(self, **kwargs):
        form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs())
        form.fields['knowledge'].queryset = Knowledge.objects.filter(user=self.request.user)
        form.fields['knowledge'].label_from_instance = lambda obj: "%s" % obj.name
        # print(form['knowledge'], form.fields['knowledge'])  # Form Field and him BoundField
        return form

    def get_success_url(self, **kwargs):
        return reverse("project_index", args=self.kwargs.values())

    def form_valid(self, form):
        topic = form.save(commit=False)
        topic.user = self.request.user
        self.object = topic
        # Category(name=form["title"].value(), user=self.request.user, topic=self.object).save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['knowledge'] = self.kwargs.get('knowledge')
        context['username'] = 'You'
        return context


class Topics(ListView):
    template_name = 'topics_index.html'
    context_object_name = 'posts'
    paginate_by = 16

    def get_queryset(self):
        return Post.objects.filter(user__username=self.kwargs['username']).order_by('-created_on')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.kwargs.get('username')
        context['knowledge'] = self.kwargs.get('knowledge')
        context['object_list'] = get_extended_queryset_topic(self)
        return context


class TopicDetail(DetailView):
    model = Topic
    template_name = 'topics_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.kwargs.get('username')
        context['knowledge'] = self.kwargs.get('knowledge')
        return context
