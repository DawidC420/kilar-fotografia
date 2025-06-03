from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db import models
from django.utils.html import mark_safe
from .session import Session
import os

# Funkcja generująca dynamiczną ścieżkę do uploadu dla plików zdjęć.
# Pliki będą zapisywane w podkatalogu o nazwie sesji.
def session_directory_path(instance, filename):
    session_name_slug = instance.session.name.replace(' ', '_').lower()
    return os.path.join('session_photos', session_name_slug, filename)


# Definicja modelu "Photo" reprezentującego pojedyncze zdjęcie.
class Photo(models.Model):
    session = models.ForeignKey(Session, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=session_directory_path)

    def __str__(self):
        return f"Photo for {self.session.name}"

    # Metoda do generowania tagu HTML dla wyświetlania miniatury zdjęcia w panelu admina.
    def image_tag(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" style="max-height: 100px; max-width: 100px;" />')
        return "Brak obrazu"
    image_tag.short_description = 'Miniatura'

# Sygnał Django, który jest wywoływany po usunięciu obiektu Photo z bazy danych.
# Jego celem jest usunięcie fizycznego pliku zdjęcia z dysku.
@receiver(post_delete, sender=Photo)
def photo_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)