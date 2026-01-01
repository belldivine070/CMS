import csv, io, datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, DetailView, TemplateView
from django.contrib import messages
from users.models import Category, CategoryPost, Widget, WidgetPost, CustomUser, AppVariable, Role, POST_FIELD_CHOICES, NewsPost, ExternalSubscriber


def get_client_ip(request):
    """Utility to extract IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



class Index(TemplateView):
    template_name = 'portech/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hero'] = WidgetPost.objects.filter(widget__slug='home-slider', is_published=True)
        context["skills"] = CategoryPost.objects.filter(category__slug='skills', is_published=True)   
        context['team'] = CategoryPost.objects.filter(category__slug='our-team', is_published=True)
        context['design'] = CategoryPost.objects.filter(category__slug='recent-portfolio', is_published=True)
        context['faq'] = CategoryPost.objects.filter(category__slug='faq', is_published=True)
        context['why'] = CategoryPost.objects.filter(category__slug='why-choose-us', is_published=True)
        context['teams'] = Category.objects.get(slug='our-team')
        context['faqs'] = Category.objects.get(slug='faq')
        context['whyus'] = Category.objects.get(slug='why-choose-us')
        context['designs'] = Category.objects.get(slug='recent-portfolio')
        return context
    

class Blog(TemplateView):
    template_name = 'portech/blog.html'

class Portfolio(TemplateView):
    template_name = "portech/portfolio.html"

class Contact(TemplateView):
    
    template_name = "portech/contact.html"

class About(TemplateView):
    template_name = "portech/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['why'] = CategoryPost.objects.filter(category__slug='why-choose-us', is_published=True)
        context['whyus'] = Category.objects.get(slug='why-choose-us')
        context['faqs'] = Category.objects.get(slug='faq')
        context['faq'] = CategoryPost.objects.filter(category__slug='faq', is_published=True)
        context['team'] = CategoryPost.objects.filter(category__slug='our-team', is_published=True)
        context['teams'] = Category.objects.get(slug='our-team')
        return context
    

class Services(TemplateView):
    template_name = "portech/services.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["skills"] = CategoryPost.objects.filter(category__slug='skills', is_published=True)   
        return context
    
