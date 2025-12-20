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
    SALAS = [
        ('Sala 1', 'Sala 1'),
        ('Sala 2', 'Sala 2'),
        ('Sala 3', 'Sala 3'),
        ('Sala 4', 'Sala 4'),
        ('Sala 5', 'Sala 5'),
        ('Sala 6', 'Sala 6'),
    ]

    sala = forms.ChoiceField(choices=SALAS, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Funcion
        fields = ['fecha', 'hora', 'sala', 'capacidad', 'precio', 'formato', 'idioma', 'lleno']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'step': '60'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'formato': forms.Select(attrs={'class': 'form-select'}),
            'idioma': forms.Select(attrs={'class': 'form-select'}),
            'lleno': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PuntuacionForm(forms.ModelForm):
    class Meta:
        model = Puntuacion
        fields = ['valor']
        widgets = {
            'valor': forms.RadioSelect(choices=[(i, f"{i} ⭐") for i in range(1, 6)])
        }

