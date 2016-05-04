from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /report/
    url(r'^policy/(?P<policy_id>[0-9]+)/$', views.policy_details, name='policy_details'),
    # ex: /report/5/
    url(r'^fund/(?P<fund_id>[0-9]+)/$', views.fund_details, name='fund_details'),
]

