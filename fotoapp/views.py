from django.shortcuts import render, redirect, get_object_or_404
from .models import Session
from django.http import FileResponse, Http404,HttpResponseForbidden
from .utils import decrypt_path,encrypt_path
import os
from django.conf import settings


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
# Widok galerii zdjęć dla użytkownika z unikalnym tokenem dostępu.
# Sprawdza, czy istnieje sesja powiązana z tokenem.
# Ustawia flagę 'gallery_access' w sesji użytkownika, aby umożliwić podgląd zdjęć.
# Dla każdego zdjęcia generuje zaszyfrowany token ścieżki.
# Renderuje szablon galerii z listą zdjęć i ich tokenami.
    session = get_object_or_404(Session, access_token=access_token)
    photos = session.photos.all()
    request.session['gallery_access'] = True
    for photo in photos:
        photo.token = encrypt_path(photo.image.name)
    return render(request, 'fotoapp/gallery.html', {'session': session, 'photos': photos})


def serve_encrypted_image(request, token):
# Obsługuje bezpieczne serwowanie zaszyfrowanych zdjęć.
# Sprawdza, czy żądanie pochodzi z galerii (Referer zawiera '/gallery/') oraz czy zdjęcie jest ładowane jako <img> (nagłówek Sec-Fetch-Dest).
# Sprawdza, czy flaga 'gallery_access' w sesji użytkownika jest ustawiona
# Deszyfruje token zdjęcia, sprawdza istnienie pliku i zwraca go jako FileResponse.
# Jeśli weryfikacja się nie powiedzie (zły Referer, brak flagi, błędny token), zwraca błąd 403 lub 404.
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
