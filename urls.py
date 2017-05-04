from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^imageapi/token/(?P<token>.{10})/get-image/(?P<image_id>.{4})/$', views.get_image, name='get_image'),
    url(r'^imageapi/token/(?P<token>.{10})/upload-image/$', views.put_image, name='put-image'),
    url(r'^imageapi/generate-token/(?P<username>[a-zA-Z0-9_]+)/$', views.generate_token, name='generate_token')

]
