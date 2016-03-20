from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /raport/
    url(r'^$', views.index, name='index'),
    # ex: /raport/5/
    url(r'^(?P<fund_id>[0-9]+)/$', views.fund_details, name='fund_details'),
]

