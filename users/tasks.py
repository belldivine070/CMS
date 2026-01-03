import logging
from celery import shared_task, group
from django.apps import apps
from django.utils import timezone
from django.core.mail import EmailMessage, send_mail
from .models import NewsPost
from django.conf import settings


logger = logging.getLogger(__name__)





import requests
from celery import shared_task
from django.apps import apps
from django.utils import timezone
from django.core.mail import EmailMessage

@shared_task(bind=True, max_retries=3)
def send_single_email_task(self, recipient, subject, body, from_email):
    """Sends one individual email. If it fails, only this specific email retries."""
    try:
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[recipient.strip()],
        )
        msg.content_subtype = "html"
        msg.send(fail_silently=False)
        return f"Sent to {recipient}"
    except Exception as exc:
        # Retry in 30 seconds if sending fails
        raise self.retry(exc=exc, countdown=30)

@shared_task
def send_broadcast_task(post_id, recipient_list, from_email, subject=None):
    """The Master Task: Spawns individual tasks for every recipient."""
    NewsPost = apps.get_model('users', 'NewsPost')
    try:
        post = NewsPost.objects.get(id=post_id)
    except NewsPost.DoesNotExist:
        return "Post not found"
    
    email_subject = subject or getattr(post, 'subject', None) or post.title
    
    # Spawn a separate task for every single recipient
    for recipient in recipient_list:
        send_single_email_task.delay(
            recipient=recipient,
            subject=email_subject,
            body=post.content,
            from_email=from_email
        )

    # Update status to 'sent'
    post.status = 'sent'
    post.last_sent_at = timezone.now()
    post.save(update_fields=['status', 'last_sent_at'])
    return f"Queued {len(recipient_list)} individual email tasks."



@shared_task
def check_scheduled_broadcasts():
    """Celery Beat task to check for scheduled posts. Uses 'users' app label."""
    # CHANGED FROM 'portech' TO 'users' TO MATCH YOUR MODELS
    NewsPost = apps.get_model('users', 'NewsPost')
    now = timezone.now()
    
    # Find posts marked as published, still in draft/scheduled, and time has arrived
    pending_posts = NewsPost.objects.filter(
        status='draft',
        scheduled_time__lte=now
    )
    
    for post in pending_posts:
        # Assuming you have logic in the model to get recipients
        # If not, you can call send_broadcast_task.delay() here
        if hasattr(post, 'send_broadcast'):
            post.send_broadcast()

