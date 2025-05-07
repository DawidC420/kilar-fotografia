from django.contrib import admin
from django.urls import path
from fotoapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='home'),
    path('check-password/', views.check_password, name='check_password'),
    path('gallery/<str:access_token>/', views.gallery_view, name='gallery_view'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
