# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-23 20:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField()),
                ('unit_price', models.FloatField()),
                ('price_date', models.DateField()),
                ('value', models.FloatField()),
                ('currency', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='InvestmentFund',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='datapoint',
            name='fund',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='report.InvestmentFund'),
        ),
        migrations.AlterUniqueTogether(
            name='datapoint',
            unique_together=set([('fund', 'price_date')]),
        ),
    ]