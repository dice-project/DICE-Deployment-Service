# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-17 09:10
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cfy_wrapper', '0003_container_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='blueprint',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 3, 17, 9, 10, 6, 787451)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='blueprint',
            name='modified_date',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2016, 3, 17, 9, 10, 25, 765838)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='container',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 3, 17, 9, 10, 33, 829567)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='container',
            name='modified_date',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2016, 3, 17, 9, 10, 39, 198442)),
            preserve_default=False,
        ),
    ]