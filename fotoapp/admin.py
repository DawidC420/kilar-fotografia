from django.contrib import admin
from .models import Session, Photo

class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1

class SessionAdmin(admin.ModelAdmin):
    inlines = [PhotoInline]

admin.site.register(Session, SessionAdmin)
