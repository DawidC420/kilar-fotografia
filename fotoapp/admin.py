from django.contrib import admin
from .models import Session, Photo

class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1

class SessionAdmin(admin.ModelAdmin):
    inlines = [PhotoInline]
    list_display = ('name', 'password', 'access_token', 'created_at')
    actions = ['regenerate_password']

    @admin.action(description='Wygeneruj nowe hasło')
    def regenerate_password(self, request, queryset):
        for session in queryset:
            session.regenerate_password()
        self.message_user(request, f'Wygenerowano nowe hasła dla {queryset.count()} sesji.')

admin.site.register(Session, SessionAdmin)
