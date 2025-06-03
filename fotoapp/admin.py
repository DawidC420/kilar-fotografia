from django.contrib import admin
from .models import Session, Photo
from .forms import SessionAdminForm

class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    fields = ('image_tag', 'image',)
    readonly_fields = ('image_tag',)

class SessionAdmin(admin.ModelAdmin):
    form = SessionAdminForm
    inlines = [PhotoInline]

    list_display = ('name', 'password', 'access_token', 'created_at')
    actions = ['regenerate_password']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if form.cleaned_data['new_photos']:
            for f in request.FILES.getlist('new_photos'):
                Photo.objects.create(session=obj, image=f)

    @admin.action(description='Wygeneruj nowe hasło')
    def regenerate_password(self, request, queryset):
        for session in queryset:
            session.regenerate_password()
        self.message_user(request, f'Wygenerowano nowe hasła dla {queryset.count()} sesji.')

admin.site.register(Session, SessionAdmin)