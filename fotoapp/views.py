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
    # zapisz id sesji aby późniejsze widoki (panel klienta) wiedziały, której sesji dotyczy użytkownik
    request.session['gallery_session_id'] = session.id
    request.session.modified = True
    for photo in photos:
        photo.token = encrypt_path(photo.image.name)
    return render(request, 'fotoapp/gallery.html', {'session': session, 'photos': photos})


def serve_encrypted_image(request, token):
    """
    Serwuje obraz po zaszyfrowanej ścieżce.
    Dozwolone, jeśli:
      - sesja ma 'gallery_access' OR
      - referer pochodzi z /gallery/ lub z /panel-klienta (lista/zamówienie)
    Dodatkowo, jeśli nagłówek SEC-FETCH-DEST jest obecny musi być 'image' — jeśli go brak, nie blokujemy.
    """
    try:
        referer = request.META.get('HTTP_REFERER', '') or ''
        sec_fetch_dest = request.META.get('HTTP_SEC_FETCH_DEST', '') or ''

        allowed_referers = ('/gallery/', '/panel-klienta')
        referer_ok = any(r in referer for r in allowed_referers)

        # jeśli nagłówek SEC-FETCH-DEST istnieje, wymuszamy 'image'
        if sec_fetch_dest and sec_fetch_dest != 'image':
            return HttpResponseForbidden("Dostęp zabroniony. Nieprawidłowy kontekst żądania.")

        # wymagamy albo flagi w sesji, albo dopuszczającego referera
        if not request.session.get('gallery_access') and not referer_ok:
            return HttpResponseForbidden("Dostęp zabroniony. Brak sesji lub nieprawidłowy referer.")

        path = decrypt_path(token)
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError
        return FileResponse(open(full_path, 'rb'), content_type='image/jpeg')
    except FileNotFoundError:
        raise Http404("Plik nie istnieje")
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


def client_panel(request):
    if not request.session.get('gallery_access'):
        # zezwól na podgląd obrazów z historii
        request.session['gallery_access'] = True
        request.session.modified = True

    # Spróbuj pobrać aktualną sesję galerii z sesji użytkownika
    photos = []
    session_id = request.session.get('gallery_session_id')
    if session_id:
        try:
            session_obj = Session.objects.get(id=session_id)
            photos = list(session_obj.photos.all()[:6])
        except Session.DoesNotExist:
            photos = []
    else:
        # brak informacji o sesji — nie pokazuj zdjęć z innych sesji
        photos = []

    # Przygotuj dwa przykładowe zamówienia (bazujące na zdjęciach z powyższej sesji)
    orders = [
        {
            "id": 1,
            "date": "2025-10-10",
            "total": "149.97",
            "items": [
                {"photo": photos[0] if len(photos) > 0 else None, "qty": 1, "price": "49.99"},
                {"photo": photos[1] if len(photos) > 1 else None, "qty": 2, "price": "49.99"},
            ]
        },
        {
            "id": 2,
            "date": "2025-10-15",
            "total": "99.98",
            "items": [
                {"photo": photos[2] if len(photos) > 2 else None, "qty": 1, "price": "49.99"},
                {"photo": photos[3] if len(photos) > 3 else None, "qty": 1, "price": "49.99"},
            ]
        }
    ]

    # Uzupełnij thumb URL dla zdjęć
    for order in orders:
        for item in order["items"]:
            p = item.get("photo")
            if p:
                try:
                    token = encrypt_path(p.image.name)
                    item["thumb"] = request.build_absolute_uri(reverse("serve_encrypted_image", args=[token]))
                except Exception:
                    item["thumb"] = ""
            else:
                item["thumb"] = ""

    return render(request, 'fotoapp/client_panel.html', {
        'orders': orders,
    })


def client_order_detail(request, order_id: int):
    if not request.session.get('gallery_access'):
        request.session['gallery_access'] = True
        request.session.modified = True

    # jeśli brak session id — zabroń dostępu (bez info o sesji nie pokazujemy zdjęć)
    session_id = request.session.get('gallery_session_id')
    if not session_id:
        return HttpResponseForbidden("Brak informacji o sesji galerii.")

    try:
        session_obj = Session.objects.get(id=session_id)
        photos = list(session_obj.photos.all()[:6])
    except Session.DoesNotExist:
        return HttpResponseForbidden("Brak informacji o sesji galerii.")

    sample_orders = {
        1: {
            "id": 1,
            "date": "2025-10-10",
            "total": "149.97",
            "items": [
                {"photo": photos[0] if len(photos) > 0 else None, "qty": 1, "price": "49.99"},
                {"photo": photos[1] if len(photos) > 1 else None, "qty": 2, "price": "49.99"},
            ]
        },
        2: {
            "id": 2,
            "date": "2025-10-15",
            "total": "99.98",
            "items": [
                {"photo": photos[2] if len(photos) > 2 else None, "qty": 1, "price": "49.99"},
                {"photo": photos[3] if len(photos) > 3 else None, "qty": 1, "price": "49.99"},
            ]
        }
    }

    order = sample_orders.get(order_id)
    if not order:
        raise Http404("Zamówienie nie istnieje")

    # Uzupełnij thumb URL dla zdjęć i oblicz line_total jako sformatowany string
    for item in order["items"]:
        p = item.get("photo")
        if p:
            try:
                token = encrypt_path(p.image.name)
                item["thumb"] = request.build_absolute_uri(reverse("serve_encrypted_image", args=[token]))
            except Exception:
                item["thumb"] = ""
        else:
            item["thumb"] = ""

        # Oblicz wartość pozycji
        try:
            qty = int(item.get("qty", 0))
            price = float(item.get("price", 0))
            item["line_total"] = f"{(qty * price):.2f}"
        except Exception:
            item["line_total"] = "0.00"

    return render(request, 'fotoapp/order_detail.html', {
        'order': order,
    })





