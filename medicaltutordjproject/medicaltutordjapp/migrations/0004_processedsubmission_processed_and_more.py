# Generated by Django 5.1.2 on 2025-05-11 23:43

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medicaltutordjapp', '0003_alter_processedsubmission_submission_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='processedsubmission',
            name='processed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name='processedsubmission',
            index=models.Index(fields=['created_at'], name='medicaltuto_created_b24d0c_idx'),
        ),
    ]
