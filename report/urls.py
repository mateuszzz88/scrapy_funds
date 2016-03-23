from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /report/
    url(r'^$', views.index, name='index'),
    # ex: /report/5/
    url(r'^(?P<fund_id>[0-9]+)/$', views.fund_details, name='fund_details'),
]

