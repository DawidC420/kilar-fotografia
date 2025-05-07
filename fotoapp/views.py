from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from .models import Session

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
    return render(request, 'fotoapp/gallery.html', {'session': session, 'photos': photos})