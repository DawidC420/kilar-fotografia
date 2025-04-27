from django.contrib import admin
from django.urls import path
from fotoapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='home'),  # jeśli homepage to root
    path('check-password/', views.check_password, name='check_password'),
    path('gallery/<int:session_id>/', views.gallery_view, name='gallery_view'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
