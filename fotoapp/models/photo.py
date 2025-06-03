from django.db import models
from .session import Session


class Photo(models.Model):
    session = models.ForeignKey(Session, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='session_photos/')
    
    def __str__(self):
        return f"Photo for {self.session.name}"
    