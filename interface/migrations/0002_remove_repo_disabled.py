# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-04-19 00:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='repo',
            name='disabled',
        ),
    ]