# Generated migration to seed sender emails

import os

from django.db import migrations


def seed_sender_emails(apps, schema_editor):
    SenderEmail = apps.get_model('email_service', 'SenderEmail')

    # Create sender emails if they don't exist.
    # App passwords come from environment variables — never hardcode credentials.
    SenderEmail.objects.get_or_create(
        email_address='ceerasHRmanager@gmail.com',
        defaults={
            'password': os.environ.get('SENDER_HR_APP_PASSWORD', ''),
            'is_active': True
        }
    )

    SenderEmail.objects.get_or_create(
        email_address='ceerastechsupport@gmail.com',
        defaults={
            'password': os.environ.get('SENDER_SUPPORT_APP_PASSWORD', ''),
            'is_active': True
        }
    )


def reverse_seed(apps, schema_editor):
    SenderEmail = apps.get_model('email_service', 'SenderEmail')
    SenderEmail.objects.filter(
        email_address__in=['ceerasHRmanager@gmail.com', 'ceerastechsupport@gmail.com']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('email_service', '0005_emaillog_sender'),
    ]

    operations = [
        migrations.RunPython(seed_sender_emails, reverse_seed),
    ]
