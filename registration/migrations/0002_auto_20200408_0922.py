# Generated by Django 3.0.5 on 2020-04-08 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Anhang',
            new_name='Attachment',
        ),
        migrations.AlterField(
            model_name='document',
            name='document',
            field=models.FileField(upload_to='dokumente', verbose_name='document'),
        ),
        migrations.AlterField(
            model_name='document',
            name='name',
            field=models.CharField(max_length=100, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='document',
            name='order',
            field=models.PositiveIntegerField(default=0, verbose_name='order'),
        ),
        migrations.AlterField(
            model_name='document',
            name='u18',
            field=models.BooleanField(default=False, help_text='Only required for persons under 18 years.', verbose_name='u18'),
        ),
        migrations.AlterField(
            model_name='document',
            name='upload',
            field=models.BooleanField(default=False, help_text='Document needs to be signed and uploaded back to the system.', verbose_name='require upload'),
        ),
    ]