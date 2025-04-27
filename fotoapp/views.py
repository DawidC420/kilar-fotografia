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
            return redirect('gallery_view', session_id=session.id)
        except Session.DoesNotExist:
            return render(request, 'fotoapp/homepage.html', {'error': 'Nieprawidłowe hasło'})
    return redirect('home')

def gallery_view(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    photos = session.photos.all()
    return render(request, 'fotoapp/gallery.html', {'session': session, 'photos': photos})