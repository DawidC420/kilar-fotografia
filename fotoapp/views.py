# fotoapp/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.urls import reverse
import os

from .models.session import Session
from .models.photo import Photo
from .utils import decrypt_path, encrypt_path
from .cart import (
    add as cart_add,
    remove as cart_remove,
    count as cart_count,
    _cart as get_cart
)


def homepage(request):
    return render(request, 'fotoapp/homepage.html')


def oferta(request):
    return render(request, 'fotoapp/oferta.html')


def kontakt(request):
    return render(request, 'fotoapp/kontakt.html')


def check_password(request):
    if request.method == "POST":
        password = request.POST.get('password')
        try:
            session = Session.objects.get(password=password)
            session.access_token = session.generate_new_token()
            session.save()
            return redirect('gallery_view', access_token=session.access_token)
        except Session.DoesNotExist:
            return render(request, 'fotoapp/homepage.html', {'error': 'Nieprawidłowe hasło'})
    return redirect('home')


def gallery_view(request, access_token):
    """
    Widok galerii zdjęć dla użytkownika z unikalnym tokenem dostępu.
    Ustawia flagę 'gallery_access' w sesji użytkownika.
    Dla każdego zdjęcia generuje zaszyfrowany token ścieżki (do bezpiecznego serwowania).
    """
    session = get_object_or_404(Session, access_token=access_token)
    photos = session.photos.all()
    request.session['gallery_access'] = True
    for photo in photos:
        photo.token = encrypt_path(photo.image.name)
    return render(request, 'fotoapp/gallery.html', {'session': session, 'photos': photos})


def serve_encrypted_image(request, token):
    """
    Serwuje obraz po zaszyfrowanej ścieżce, tylko z widoku galerii i jako <img>.
    """
    try:
        referer = request.META.get('HTTP_REFERER', '')
        sec_fetch_dest = request.META.get('HTTP_SEC_FETCH_DEST', '')
        if not referer or '/gallery/' not in referer:
            return HttpResponseForbidden("Dostęp zabroniony. Brak sesji.")
        if not request.session.get('gallery_access'):
            return HttpResponseForbidden("Dostęp zabroniony. Brak sesji.")
        if sec_fetch_dest != 'image':
            return HttpResponseForbidden("Dostęp zabroniony. Brak sesji.")
        path = decrypt_path(token)
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError
        return FileResponse(open(full_path, 'rb'), content_type='image/jpeg')
    except Exception:
        raise Http404("Błędny token lub plik nie istnieje")


# ===============================
#             KOSZYK
# ===============================

@require_POST
def api_cart_add(request, photo_id: int):
    """
    Dodaje 1 szt. zdjęcia do koszyka (sesja). Zwraca JSON z aktualnym licznikiem.
    """
    try:
        p = Photo.objects.get(pk=photo_id)
    except Photo.DoesNotExist:
        raise Http404("Photo not found")

    cart_add(request, photo_id=p.id, price=p.price, qty=1)
    return JsonResponse({"ok": True, "count": cart_count(request)})


@require_POST
def api_cart_remove(request, photo_id: int):
    """
    Usuwa 1 szt. zdjęcia z koszyka (sesja). Zwraca JSON z aktualnym licznikiem.
    """
    try:
        p = Photo.objects.get(pk=photo_id)
    except Photo.DoesNotExist:
        raise Http404("Photo not found")

    cart_remove(request, photo_id=p.id, qty=1)
    return JsonResponse({"ok": True, "count": cart_count(request)})


@require_POST
def api_cart_delete(request, photo_id: int):
    """
    Usuwa CAŁĄ pozycję z koszyka (zeroje qty). Do użycia w mini-koszyku przy przycisku „Usuń”.
    """
    cart = get_cart(request)  # dict w sesji
    cart.pop(str(photo_id), None)
    request.session.modified = True
    return JsonResponse({"ok": True, "count": cart_count(request)})


def api_cart_summary(request):
    """
    Zwraca JSON z zawartością koszyka (mini-koszyk):
    {
      "ok": true,
      "items": [{"id":1,"qty":1,"price":"49.99","line_total":"49.99","thumb":"..."}],
      "total":"149.97",
      "count":3
    }
    """
    cart = get_cart(request)  # np. {'12': {'qty': 2, 'price': '49.99'}, ...}
    if not cart:
        return JsonResponse({"ok": True, "items": [], "total": "0.00", "count": 0})

    ids = [int(pid) for pid in cart.keys()]
    photos = Photo.objects.filter(id__in=ids)
    photos_map = {p.id: p for p in photos}

    items = []
    total = 0.0

    for pid_str, entry in cart.items():
        pid = int(pid_str)
        p = photos_map.get(pid)
        if not p:
            continue
        qty = int(entry.get("qty", 0))
        price = float(entry.get("price", 0))
        line_total = qty * price
        total += line_total

        token = encrypt_path(p.image.name)
        thumb_url = request.build_absolute_uri(
            reverse("serve_encrypted_image", args=[token])
        )

        items.append({
            "id": pid,
            "qty": qty,
            "price": f"{price:.2f}",
            "line_total": f"{line_total:.2f}",
            "thumb": thumb_url,
        })

    return JsonResponse({
        "ok": True,
        "items": items,
        "total": f"{total:.2f}",
        "count": sum(i["qty"] for i in cart.values()),
    })


def cart_view(request):
    """
    (Opcjonalny fallback) Prosty widok koszyka – można go zachować, choć mini-koszyk działa w modalu.
    """
    return render(request, "cart/view.html", {"cart": get_cart(request)})
