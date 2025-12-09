from django.contrib import admin
from .models import Session, Photo
from .forms import SessionAdminForm
from .models.order import Order, OrderItem

# Inline do zarządzania pojedyńczymi zdjęciami na stronie edycji Session.
class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 0
    fields = ('image_tag', 'image',)
    readonly_fields = ('image_tag',)

# Definiuje, jak model Session będzie wyświetlany i zarządzany w adminie.
class SessionAdmin(admin.ModelAdmin):
    form = SessionAdminForm
    inlines = [PhotoInline]
    list_display = ('name', 'password', 'access_token', 'created_at')
    actions = ['regenerate_password']

    # Nadpisanie metody save_model, która jest wywoływana po zapisaniu formularza w adminie.
    # Wykorzystywana do obsługi przesyłanych wielu zdjęć.
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if form.cleaned_data['new_photos']:
            for f in request.FILES.getlist('new_photos'):
                Photo.objects.create(session=obj, image=f)

    # Iteruje przez wybrane obiekty Session i regeneruje dla każdego hasło.
    @admin.action(description='Wygeneruj nowe hasło')
    def regenerate_password(self, request, queryset):
        for session in queryset:
            session.regenerate_password()
        self.message_user(request, f'Wygenerowano nowe hasła dla {queryset.count()} sesji.')

admin.site.register(Session, SessionAdmin)




# ===============================
# Rejestracja modelu Order w adminie
# - OrderItemInline pokazuje wszystkie pozycje zamówienia w formularzu Order
# - OrderAdmin pokazuje listę zamówień z kolumnami ID, email, data, suma, session_key
#   oraz umożliwia wyszukiwanie po emailu i sesji
# - Dzięki inline admin od razu widzi wszystkie zdjęcia i ceny w zamówieniu
# ===============================


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('photo', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'date', 'total', 'session_key')
    search_fields = ('email', 'session_key')
    inlines = [OrderItemInline]



