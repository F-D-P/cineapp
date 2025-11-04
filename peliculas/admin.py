from django.contrib import admin
from .models import Pelicula, Funcion, Puntuacion

@admin.register(Pelicula)
class PeliculaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'genero', 'duracion', 'fecha_estreno', 'es_estreno', 'mostrar_promedio')
    fields = ('titulo', 'director', 'genero', 'duracion', 'fecha_estreno', 'sinopsis', 'imagen', 'es_estreno')
    readonly_fields = ('mostrar_promedio',)

    def mostrar_promedio(self, obj):
        return obj.promedio_puntuacion()
    mostrar_promedio.short_description = "Promedio de puntuación"

@admin.register(Funcion)
class FuncionAdmin(admin.ModelAdmin):
    list_display = ('pelicula', 'fecha', 'hora', 'sala')

@admin.register(Puntuacion)
class PuntuacionAdmin(admin.ModelAdmin):
    list_display = ('pelicula', 'valor', 'fecha')