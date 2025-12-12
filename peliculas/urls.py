from django.urls import path, include
from django.shortcuts import redirect
from . import views
from .views import (
    PeliculaCreateView,
    PeliculaUpdateView,
    PeliculaDeleteView,
)
from .views import seleccionar_asientos, confirmar_reserva

urlpatterns = [
    # Página principal
    path('', views.inicio, name='inicio'),
    path('peliculas/', views.inicio, name='lista_peliculas'),

    # Detalle y gestión de películas
    path('pelicula/<int:pk>/', views.detalle_pelicula, name='detalle_pelicula'),
    path('agregar/', PeliculaCreateView.as_view(), name='agregar_pelicula'),
    path('editar/<int:pk>/', PeliculaUpdateView.as_view(), name='editar_pelicula'),
    path('eliminar/<int:pk>/', PeliculaDeleteView.as_view(), name='eliminar_pelicula'),
    path('pelicula/<int:pk>/funciones/', views.funciones_pelicula, name='funciones_pelicula'),
    path('reservar/', views.reservar_entrada, name='reservar_entrada'),
    path('soporte/', views.soporte, name='soporte'),
    path('mis-entradas/', views.mis_entradas, name='mis_entradas'),
    path('funcion/<int:funcion_id>/asientos/', seleccionar_asientos, name='seleccionar_asientos'),
    path('funcion/<int:funcion_id>/confirmar/', confirmar_reserva, name='confirmar_reserva'),
    path('pelicula/<int:pk>/comprar/', views.funciones_disponibles, name='funciones_disponibles'),
    path('funcion/<int:pk>/editar/', views.editar_funcion, name='editar_funcion'),
    path('funcion/<int:pk>/eliminar/', views.eliminar_funcion, name='eliminar_funcion'),
    path('pelicula/<int:pelicula_id>/funcion/nueva/', views.agregar_funcion, name='agregar_funcion'),
    path("checkout/<int:reserva_id>/", views.checkout, name="checkout"),
    path("pago-exitoso/<int:reserva_id>/", views.pago_exitoso, name="pago_exitoso"),
    path("pago-fallido/<int:reserva_id>/", views.pago_fallido, name="pago_fallido"),
    path("mp-webhook/", views.mp_webhook, name="mp_webhook"),

    # Búsqueda
    path('buscar/', views.buscar_pelicula, name='buscar_pelicula'),

    # Autenticación
    path('login/', lambda request: redirect('account_login')),  # ✅ Redirige a django-allauth
    path('signup/', views.signup, name='registro'),             # ✅ Vista personalizada si la tenés
    path('accounts/', include('allauth.urls')),                 # ✅ Incluye todo el flujo de allauth

    # Tarjetas
    path("pago_tarjeta/<int:reserva_id>/", views.pago_tarjeta, name="pago_tarjeta"),
    path("mp_card_payment/<int:reserva_id>/", views.mp_card_payment, name="mp_card_payment"),


]