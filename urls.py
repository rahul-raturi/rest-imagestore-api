from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^imageapi/token/(?P<token>.{10})/get-image/(?P<image_id>.{4})/$', views.get_image, name='get_image'),
    url(r'^imageapi/token/(?P<token>.{10})/upload-image/$', views.put_image, name='put-image'),
    url(r'^imageapi/generate-token/(?P<username>[a-zA-Z0-9_]+)/$', views.generate_token, name='generate_token'),
    url(r'^imageapi/retrieve-token/(?P<username>[a-zA-Z0-9_]+)/$', views.retrieve_token, name='retrieve_token'),
    url(r'^imageapi/token/(?P<token>.{10})/get-image-list/$', views.get_image_list, name='get_image_list'),
    url(r'^imageapi/token/(?P<token>.{10})/delete-image/(?P<image_id>.{4})/$', views.remove_image, name='remove_image'),
]
