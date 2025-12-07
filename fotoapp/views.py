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
    Wyświetla galerię zdjęć dla danego tokenu dostępu.
    Ustawia flagi sesji dla dalszego dostępu.
    """
    session = get_object_or_404(Session, access_token=access_token)
    photos = session.photos.all()
    request.session['gallery_access'] = True
    request.session['gallery_session_id'] = session.id
    request.session.modified = True
    
    for photo in photos:
        photo.token = encrypt_path(photo.image.name)
    
    return render(request, 'fotoapp/gallery.html', {
        'session': session,
        'photos': photos
    })


def serve_encrypted_image(request, token):
    """
    Serwuje obraz po zaszyfrowanej ścieżce.
    Dostęp dozwolony jeśli:
      - sesja ma 'gallery_access' OR
      - referer pochodzi z /gallery/ lub /panel-klienta
    """
    try:
        referer = request.META.get('HTTP_REFERER', '') or ''
        sec_fetch_dest = request.META.get('HTTP_SEC_FETCH_DEST', '') or ''

        allowed_referers = ('/gallery/', '/panel-klienta')
        referer_ok = any(r in referer for r in allowed_referers)

        #Odmowa dostępu jeśli żądanie nie pochodzi z kontekstu obrazu
        if sec_fetch_dest and sec_fetch_dest != 'image':
            return HttpResponseForbidden("Dostęp zabroniony. Nieprawidłowy kontekst żądania.")
        # Odmowa jeśli brak sesji i niepoprawny referer
        if not request.session.get('gallery_access') and not referer_ok:
            return HttpResponseForbidden("Dostęp zabroniony. Brak sesji lub nieprawidłowy referer.")

        path = decrypt_path(token)
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError
        
        return FileResponse(open(full_path, 'rb'), content_type='image/jpeg')

    except (FileNotFoundError, Exception):
        raise Http404("Plik nie istnieje lub token jest błędny")

def client_panel(request):
    """
    Panel klienta — wyświetla historię zamówień i miniaturki zdjęć.
    W przyszłości pobieranie zamówień z bazy danych.
    """
    if not request.session.get('gallery_access'):
        request.session['gallery_access'] = True
        request.session.modified = True

    session_id = request.session.get('gallery_session_id')
    gallery_url = None
    orders = []

    if session_id:
        try:
            session_obj = Session.objects.get(id=session_id)
            # Miniaturki dla  zdjęć w panelu
            photos = list(session_obj.photos.all())
            gallery_url = reverse('gallery_view', args=[session_obj.access_token])

            # W przyszłości tutaj pobierzemy zamówienia z bazy:
            # orders = Order.objects.filter(session=session_obj).order_by('-date')
            # dla każdego orderu dodamy linki do miniatur i zdjęć
            # obecnie zostawiamy puste listy

        except Session.DoesNotExist:
            photos = []
            gallery_url = None

    return render(request, 'fotoapp/klient/client_panel.html', {
        'orders': orders,
        'gallery_url': gallery_url,
    })


def client_order_detail(request, order_id: int):
    """
    Szczegóły zamówienia klienta.
    Obecnie brak danych — w przyszłości pobieranie z bazy.
    """
    if not request.session.get('gallery_access'):
        request.session['gallery_access'] = True
        request.session.modified = True

    session_id = request.session.get('gallery_session_id')
    if not session_id:
        return HttpResponseForbidden("Brak informacji o sesji galerii.")

    try:
        session_obj = Session.objects.get(id=session_id)
        photos = list(session_obj.photos.all()[:6])
    except Session.DoesNotExist:
        return HttpResponseForbidden("Brak informacji o sesji galerii.")

    # W przyszłości pobranie zamówienia z bazy
    # order = Order.objects.get(id=order_id, session=session_obj)
    # items = order.items.all()
    # dla każdego item generujemy token + thumb + download_url

    order = {
        "id": order_id,
        "date": None,
        "total": None,
        "items": []
    }

    return render(request, 'fotoapp/klient/order_detail.html', {
        'order': order,
    })

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
