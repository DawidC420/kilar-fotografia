from django import forms
from .models import Session

# Niestandardowy widżet HTML do wyboru wielu plików jednocześnie.
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True 

# Niestandardowe pole formularza do obsługi wielu plików.
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    # Waliduje wiele przesłanych plików, jeśli są podane jako lista.
    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            result = [super().clean(d, initial) for d in data]
        else:
            result = super().clean(data, initial)
        return result

# Formularz dla modelu Session w panelu administracyjnym.
# Rozszerza go o pole do masowego przesyłania zdjęć.
class SessionAdminForm(forms.ModelForm):
    new_photos = MultipleFileField(label='Wgraj wiele zdjęć', required=False)

    class Meta:
        model = Session
        fields = '__all__'