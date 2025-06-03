import uuid
from django.db import models
from django.utils.crypto import get_random_string
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.conf import settings
import os



class Session(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    password = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    access_token = models.CharField(max_length=36, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.access_token:
            self.access_token = str(uuid.uuid4())

        if not self.password:
            self.password = self.generate_new_password()

        super().save(*args, **kwargs)
    
    def generate_new_password(self):
        return get_random_string(12)
    
    def generate_new_token(self):
        return str(uuid.uuid4())
    
    def regenerate_password(self):
        self.password = self.generate_new_password()
        self.save()

    def __str__(self):
        return self.name

@receiver(post_delete, sender=Session)
def session_delete(sender, instance, **kwargs):
    session_name_slug = instance.name.replace(' ', '_').lower()
    session_dir = os.path.join(settings.MEDIA_ROOT, 'session_photos', session_name_slug)

    if os.path.isdir(session_dir):
        if not os.listdir(session_dir):
            os.rmdir(session_dir)
