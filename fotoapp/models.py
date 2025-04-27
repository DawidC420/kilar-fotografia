from django.db import models

class Session(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    password = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Photo(models.Model):
    session = models.ForeignKey(Session, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='session_photos/')

    def __str__(self):
        return f"Photo for {self.session.name}"
