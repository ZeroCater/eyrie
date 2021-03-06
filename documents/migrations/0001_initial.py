# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-04-14 22:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('interface', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.TextField()),
                ('filename', models.TextField()),
                ('body', models.TextField(blank=True)),
                ('commit_date', models.DateTimeField()),
                ('repo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='interface.Repo')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together=set([('repo', 'path', 'filename')]),
        ),
    ]
