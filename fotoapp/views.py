from django.shortcuts import render, redirect, get_object_or_404
from .models import Session, Photo
from django.http import FileResponse, Http404,HttpResponseForbidden
from .utils import decrypt_path,encrypt_path
import os
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required


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
    session = get_object_or_404(Session, access_token=access_token)
    photos = session.photos.all()
    request.session['gallery_access'] = True
    for photo in photos:
        photo.token = encrypt_path(photo.image.name)
    return render(request, 'fotoapp/gallery.html', {'session': session, 'photos': photos})


def serve_encrypted_image(request, token):
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
