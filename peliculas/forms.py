from django import forms
from .models import Pelicula, Funcion, Puntuacion, Sala

class PeliculaForm(forms.ModelForm):
    class Meta:
        model = Pelicula
        fields = [
            'titulo', 'director', 'genero',
            'fecha_estreno', 'sinopsis',
            'imagen', 'es_estreno', 'duracion'
        ]
        widgets = {
            'fecha_estreno': forms.DateInput(attrs={'type': 'date'}),
            'sinopsis': forms.Textarea(attrs={'rows': 4}),
            'duracion': forms.NumberInput(attrs={'placeholder': 'Duración en minutos'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class FuncionForm(forms.ModelForm):
    class Meta:
        model = Funcion
        fields = ['fecha', 'hora', 'sala', 'capacidad', 'precio', 'formato', 'idioma', 'lleno']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'sala': forms.Select(attrs={'class': 'form-select'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'formato': forms.Select(attrs={'class': 'form-select'}),
            'idioma': forms.Select(attrs={'class': 'form-select'}),
            'lleno': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sala'] = forms.ModelChoiceField(
            queryset=Sala.objects.filter(activa=True),
            widget=forms.Select(attrs={'class': 'form-select'})
        )


class PuntuacionForm(forms.ModelForm):
    class Meta:
        model = Puntuacion
        fields = ['valor']
        widgets = {
            'valor': forms.RadioSelect(choices=[(i, f"{i} ⭐") for i in range(1, 6)])
        }

