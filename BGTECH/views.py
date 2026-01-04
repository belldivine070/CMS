import csv, io, datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, DetailView, TemplateView
from django.contrib import messages
from users.models import Category, CategoryPost, Widget, WidgetPost, NewsPost, ExternalSubscriber
from users.views import SubcribersHubView
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.views.generic.edit import FormView
from users.utils import get_client_ip 
from .forms import SubcribersForm
from django.contrib.gis.geoip2 import GeoIP2
from django.contrib import messages




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




class External(FormView):
    template_name = 'portech/index.html'
    form_class = SubcribersForm
    success_url = reverse_lazy('portech:home')  

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        
        # 1. Check for existing subscriber
        if ExternalSubscriber.objects.filter(email=email).exists():
            messages.warning(self.request, "This email is already subscribed.")
            return HttpResponseRedirect(self.success_url)

        # 2. Initialize instance and IP
        subscriber = form.save(commit=False)
        ip = get_client_ip(self.request)
        subscriber.ip_address = ip 

        # 3. Geo Tracking with Error Handling
        try:
            g = GeoIP2()
            location = g.city(ip)
            
            # Match these keys to your model fields (city, region, country)
            subscriber.city = location.get('city')
            subscriber.region = location.get('region')
            subscriber.country = location.get('country_name')
            
            # Optional: if you add these to your model later
            # subscriber.latitude = location.get('latitude')
            # subscriber.longitude = location.get('longitude')
            
        except Exception as e:
            # This catches missing GEOIP_PATH, missing .mmdb files, or local IPs
            print(f"GeoIP Error for IP {ip}: {e}")

        # 4. Save to Database
        subscriber.save()
        
        # 5. Success Message
        messages.success(self.request, "Thank you for subscribing!")
        return HttpResponseRedirect(self.success_url)


# class External(FormView):
#     template_name = 'portech/index.html'
#     form_class = SubcribersForm
#     success_url = reverse_lazy('portech:home')  

#     def get_absolute_url(self):
#         return reverse_lazy('portech:home')
    
#     def form_valid(self, form):
#         email = form.cleaned_data.get("email")
        
#         # Check for existing subscriber
#         if ExternalSubscriber.objects.filter(email=email).exists():
#             messages.warning(self.request, "This email is already subscribed.")
#             return HttpResponseRedirect(self.success_url)

#         subscriber = form.save(commit=False)
#         ip = get_client_ip(self.request)
#         subscriber.ip_address = ip 

#         # --- REAL-TIME GEO TRACKING ---
#         g = GeoIP2()
#         try:
#             # Use 'city' to get detailed info or 'country' for just the nation
#             location = g.city(ip)
#             subscriber.city = location.get('city')
#             subscriber.country_code = location.get('country_code')
#             subscriber.latitude = location.get('latitude')
#             subscriber.longitude = location.get('longitude')
#         except Exception as e:
#             # Handle cases where IP is local (127.0.0.1) or not in database
#             print(f"GeoIP Error: {e}")

#         subscriber.save()
#         messages.success(self.request, "Subscriber added successfully!")
#         return HttpResponseRedirect(self.success_url)