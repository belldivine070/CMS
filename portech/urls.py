from django.urls import path
from . import views


# app_name = 'portech' 


urlpatterns = [
    path('', views.Index.as_view(), name='home'),
    path('services/', views.Services.as_view(), name='services'),
    path('blog/', views.Blog.as_view(), name='blog'),
    path('contact/', views.Contact.as_view(), name='contact'),
    path('portfolio/', views.Portfolio.as_view(), name='portfolio'),
    path('about/', views.About.as_view(), name='about')
]
