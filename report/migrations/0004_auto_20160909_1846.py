# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-09-09 18:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0003_policyoperationdetail'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='policyoperationdetail',
            unique_together=set([('fund', 'operation')]),
        ),
    ]
