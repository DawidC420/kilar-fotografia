from django.contrib import admin
from django.urls import path
from fotoapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='home'),
    path('oferta/', views.oferta, name='oferta'),
    path('kontakt/', views.kontakt, name='kontakt'),
    path('check-password/', views.check_password, name='check_password'),
    path('gallery/<str:access_token>/', views.gallery_view, name='gallery_view'),
    path('image/<str:token>/', views.serve_encrypted_image, name='serve_encrypted_image'),
    #koszyk
    path("api/cart/add/<int:photo_id>/", views.api_cart_add, name="api_cart_add"),
    path("api/cart/remove/<int:photo_id>/", views.api_cart_remove, name="api_cart_remove"),
    path("cart/", views.cart_view, name="cart_view"),
    path("api/cart/summary/", views.api_cart_summary, name="api_cart_summary"),
    path("api/cart/delete/<int:photo_id>/", views.api_cart_delete, name="api_cart_delete"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
