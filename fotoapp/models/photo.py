from django.db import models
from django.utils.html import mark_safe
from .session import Session


class Photo(models.Model):
    session = models.ForeignKey(Session, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='session_photos/')

    def __str__(self):
        return f"Photo for {self.session.name}"

    def image_tag(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" style="max-height: 100px; max-width: 100px;" />')
        return "Brak obrazu"
    image_tag.short_description = 'Miniatura'