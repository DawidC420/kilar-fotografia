from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from .models import Session
from django.http import FileResponse, Http404
from .utils import decrypt_path
import os
from django.conf import settings
from .utils import encrypt_path


def homepage(request):
    return render(request, 'fotoapp/homepage.html')

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

    encrypted_photos = []
    for photo in photos:
        relative_path = photo.image.name  
        token = encrypt_path(relative_path)
        encrypted_photos.append({
            'token': token,
            'id': photo.id,
        })

    # Łączenie Photo i token 
    photos_data = zip(photos, encrypted_photos)
    return render(request, 'fotoapp/gallery.html', {
        'session': session,
        'photos_data': photos_data,
    })




def serve_encrypted_image(request, token):
    try:
        relative_path = decrypt_path(token)
    except Exception:
        raise Http404("Nieprawidłowy token")

    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    if not os.path.isfile(full_path):
        raise Http404("Plik nie istnieje")

    return FileResponse(open(full_path, 'rb'), content_type='image/jpeg')

