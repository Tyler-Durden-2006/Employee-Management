import logging
import mimetypes
import os

from rest_framework import viewsets
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMessage, get_connection

from .models import EmailLog, EmailTemplate, SenderEmail
from .serializers import (
    EmailLogSerializer,
    EmailTemplateSerializer,
    SenderEmailSerializer,
)
from history.models import EmailHistory

logger = logging.getLogger(__name__)


class EmailLogViewSet(viewsets.ModelViewSet):
    queryset = EmailLog.objects.all()
    serializer_class = EmailLogSerializer

    def perform_create(self, serializer):
        # Save email initially
        email = serializer.save()
        email.status = "Sending"
        email.save()

        # Get selected sender
        sender = email.sender

        if not sender:
            email.status = "Failed"
            email.sent_at = timezone.now()
            email.save()

            logger.error(
                f"No sender email selected for email to {email.recipient_email}"
            )

            EmailHistory.objects.create(
                employee=email.employee,
                sender=email.sender,
                recipient_email=email.recipient_email,
                subject=email.subject,
                message=email.message,
                status=email.status,
                retry_count=email.retry_count,
                sent_at=email.sent_at,
            )

            return

        # Create SMTP connection using sender credentials.
        # When email credentials are absent, settings.py configures the console
        # backend for development — honour that instead of forcing real SMTP.
        if settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
            connection = get_connection(
                backend="django.core.mail.backends.smtp.EmailBackend",
                host="smtp.gmail.com",
                port=587,
                username=sender.email_address,
                password=sender.password,
                use_tls=True,
            )
        else:
            connection = get_connection()

        # Create email
        email_message = EmailMessage(
            subject=email.subject,
            body=email.message,
            from_email=sender.email_address,
            to=[email.recipient_email],
            connection=connection,
        )

        # Attachment support
        attachment_file = (
            self.request.FILES.get("attachment")
            or self.request.data.get("attachment")
        )

        if attachment_file:
            attachment_file.seek(0)
            content = attachment_file.read()
            attachment_file.seek(0)

            filename = attachment_file.name
            content_type = attachment_file.content_type

            if content.startswith(b"%PDF-"):
                content_type = "application/pdf"

                if not filename.lower().endswith(".pdf"):
                    filename = (
                        f"{os.path.splitext(filename)[0]}.pdf"
                    )

            else:
                guessed_type, _ = mimetypes.guess_type(filename)

                if guessed_type:
                    content_type = guessed_type
                elif not content_type:
                    content_type = "application/octet-stream"

            email_message.attach(
                filename,
                content,
                content_type,
            )

        # Send email
        try:
            email_message.send(fail_silently=False)

            email.status = "Sent"

            logger.info(
                f"Email sent successfully from "
                f"{sender.email_address} "
                f"to {email.recipient_email}"
            )

        except Exception as e:

            logger.exception(
                f"Failed to send email from "
                f"{sender.email_address} "
                f"to {email.recipient_email}: {str(e)}"
            )

            email.status = "Failed"

        email.sent_at = timezone.now()
        email.save()

        # Save history
        EmailHistory.objects.create(
            employee=email.employee,
            sender=email.sender,
            recipient_email=email.recipient_email,
            subject=email.subject,
            message=email.message,
            status=email.status,
            retry_count=email.retry_count,
            sent_at=email.sent_at,
        )


class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer


class SenderEmailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SenderEmail.objects.filter(is_active=True)
    serializer_class = SenderEmailSerializer