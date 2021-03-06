# Generated by Django 3.0.5 on 2020-04-08 09:27

import ckeditor_uploader.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_auto_20200408_0924'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebPage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(default='home')),
                ('name', models.CharField(max_length=30)),
                ('icon', models.CharField(default='home', help_text='Name of a fontawesome icon to display in the menu', max_length=30)),
                ('html', ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('menu', models.BooleanField(default=True, verbose_name='Visible in the menu')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seiten', to='registration.Event')),
            ],
            options={
                'verbose_name': 'page',
                'verbose_name_plural': 'pages',
                'ordering': ('order',),
                'unique_together': {('event', 'slug')},
            },
        ),
        migrations.DeleteModel(
            name='Seite',
        ),
    ]
