# Django genéricas (CBV)
from django.views.generic import CreateView, UpdateView, DeleteView

# Modelos y formularios
from .models import Pelicula, Reserva, Funcion, Asiento, Entrada, Sala
from .forms import PeliculaForm, PuntuacionForm, FuncionForm

# Utilidades de Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.urls import reverse, reverse_lazy
from django.utils import timezone

# Extras
from io import BytesIO
from django.core.files import File
import qrcode
import json
import random
import string
import mercadopago
import logging

# Configuración global
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from .models import Pelicula, Funcion

# Logger para registrar errores
logger = logging.getLogger(__name__)

# ---------------------------
# Rankings y página de inicio
# ---------------------------

def top5_taquilla():
    hoy = timezone.now().date()
    lunes_actual = hoy - timezone.timedelta(days=hoy.weekday())
    lunes_anterior = lunes_actual - timezone.timedelta(days=7)

    reservas = (Reserva.objects
        .filter(estado__in=['pagada', 'validada'],
                fecha_creacion__gte=lunes_anterior,
                fecha_creacion__lt=lunes_actual)
        .values('funcion__pelicula__id', 'funcion__pelicula__titulo')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5])
    return reservas

def inicio(request):
    genero = request.GET.get('genero')
    query = request.GET.get('q')
    generos_validos = [g[0] for g in Pelicula._meta.get_field('genero').choices]
    catalogo = Pelicula.objects.filter(es_estreno=False)

    if genero in generos_validos:
        catalogo = catalogo.filter(genero=genero)
    if query:
        catalogo = catalogo.filter(
            Q(titulo__icontains=query) |
            Q(genero__icontains=query) |
            Q(director__icontains=query)
        )

    proximamente = Pelicula.objects.filter(es_estreno=True).order_by('fecha_estreno')[:5]

    return render(request, 'peliculas/inicio.html', {
        'catalogo': catalogo,
        'proximamente': proximamente,
        'top_taquilla': top5_taquilla(),
        'genero_actual': genero,
        'query': query,
    })

def buscar_pelicula(request):
    query = request.GET.get('q', '')
    resultados = Pelicula.objects.filter(
        Q(titulo__icontains=query) |
        Q(genero__icontains=query) |
        Q(director__icontains=query)
    )
    return render(request, 'peliculas/buscar.html', {
        'query': query,
        'resultados': resultados,
    })

# ---------------------------
# Rankings y página de inicio
# ---------------------------

def top5_taquilla():
    hoy = timezone.now().date()
    lunes_actual = hoy - timezone.timedelta(days=hoy.weekday())
    lunes_anterior = lunes_actual - timezone.timedelta(days=7)

    reservas = (Reserva.objects
        .filter(estado__in=['pagada', 'validada'],
                fecha_creacion__gte=lunes_anterior,
                fecha_creacion__lt=lunes_actual)
        .values('funcion__pelicula__id', 'funcion__pelicula__titulo')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5])
    return reservas

def inicio(request):
    genero = request.GET.get('genero')
    query = request.GET.get('q')
    generos_validos = [g[0] for g in Pelicula._meta.get_field('genero').choices]
    catalogo = Pelicula.objects.filter(es_estreno=False)

    if genero in generos_validos:
        catalogo = catalogo.filter(genero=genero)
    if query:
        catalogo = catalogo.filter(
            Q(titulo__icontains=query) |
            Q(genero__icontains=query) |
            Q(director__icontains=query)
        )

    proximamente = Pelicula.objects.filter(es_estreno=True).order_by('fecha_estreno')[:5]

    return render(request, 'peliculas/inicio.html', {
        'catalogo': catalogo,
        'proximamente': proximamente,
        'top_taquilla': top5_taquilla(),
        'genero_actual': genero,
        'query': query,
    })

def buscar_pelicula(request):
    query = request.GET.get('q', '')
    resultados = Pelicula.objects.filter(
        Q(titulo__icontains=query) |
        Q(genero__icontains=query) |
        Q(director__icontains=query)
    )
    return render(request, 'peliculas/buscar.html', {
        'query': query,
        'resultados': resultados,
    })

# ---------------------------
# CRUD Películas
# ---------------------------

def agregar_pelicula(request):
    if request.method == 'POST':
        form = PeliculaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_peliculas')
    else:
        form = PeliculaForm()
    return render(request, 'peliculas/agregar.html', {'form': form})

def detalle_pelicula(request, pk):
    pelicula = get_object_or_404(Pelicula, id=pk)
    form = PuntuacionForm()
    voto_exitoso = False
    if request.method == 'POST':
        form = PuntuacionForm(request.POST)
        if form.is_valid():
            puntuacion = form.save(commit=False)
            puntuacion.pelicula = pelicula
            puntuacion.save()
            voto_exitoso = True
    promedio = pelicula.promedio_puntuacion()
    return render(request, 'peliculas/detalle.html', {
        'pelicula': pelicula,
        'form': form,
        'promedio': promedio,
        'voto_exitoso': voto_exitoso,
    })

class PeliculaCreateView(CreateView):
    model = Pelicula
    form_class = PeliculaForm
    template_name = 'peliculas/formulario.html'
    success_url = reverse_lazy('inicio')

class PeliculaUpdateView(UpdateView):
    model = Pelicula
    form_class = PeliculaForm
    template_name = 'peliculas/formulario.html'
    success_url = reverse_lazy('inicio')

class PeliculaDeleteView(DeleteView):
    model = Pelicula
    template_name = 'peliculas/confirmar_eliminacion.html'
    success_url = reverse_lazy('inicio')

# ---------------------------
# Funciones y reservas
# ---------------------------

def generar_asientos(funcion):
    filas = ['A','B','C','D','E','F','G']
    for fila in filas:
        for numero in range(0, 11):  # 0..10
            funcion.asientos.create(fila=fila, numero=numero)

@login_required
def reservar_entrada(request):
    funciones = Funcion.objects.select_related('pelicula').order_by('fecha', 'hora')
    if request.method == 'POST':
        funcion_id = request.POST.get('funcion')
        cantidad = request.POST.get('cantidad')
        funcion = get_object_or_404(Funcion, id=funcion_id)
        Reserva.objects.create(
            usuario=request.user,
            funcion=funcion,
            cantidad=cantidad,
            estado="pendiente"
        )
        return redirect('mis_entradas')
    return render(request, 'peliculas/reservar_entrada.html', {'funciones': funciones})

@login_required
def seleccionar_asientos(request, funcion_id):
    funcion = get_object_or_404(Funcion, id=funcion_id)
    filas = ['A','B','C','D','E','F']
    columnas = list(range(1, 11))
    asientos = Asiento.objects.filter(funcion=funcion).order_by('fila', 'numero')
    return render(request, 'peliculas/seleccionar_asientos.html', {
        'funcion': funcion,
        'filas': filas,
        'columnas': columnas,
        'asientos': asientos,
    })

@login_required
def confirmar_reserva(request, funcion_id):
    funcion = get_object_or_404(Funcion, id=funcion_id)
    ids = request.POST.get('asientos_seleccionados', '').split(',')
    asientos_confirmados = []
    for asiento_id in ids:
        if asiento_id:
            asiento = get_object_or_404(Asiento, id=asiento_id, funcion=funcion)
            if asiento.estado == 'libre':
                asiento.estado = 'ocupado'
                asiento.save()
                asientos_confirmados.append(asiento)
    if asientos_confirmados:
        reserva = Reserva.objects.create(
            usuario=request.user,
            funcion=funcion,
            cantidad=len(asientos_confirmados),
            estado="pendiente"
        )
        reserva.asientos.set(asientos_confirmados)
        return redirect("checkout", reserva_id=reserva.id)
    return redirect("seleccionar_asientos", funcion_id=funcion.id)

@user_passes_test(lambda u: u.is_staff)
def funciones_pelicula(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    funciones = pelicula.funciones.all().order_by('fecha', 'hora')
    if request.method == 'POST':
        form = FuncionForm(request.POST)
        if form.is_valid():
            nueva_funcion = form.save(commit=False)
            nueva_funcion.pelicula = pelicula
            nueva_funcion.save()
            generar_asientos(nueva_funcion)
            return redirect('funciones_pelicula', pk=pelicula.pk)
    else:
        form = FuncionForm()
    return render(request, 'peliculas/funciones_pelicula.html', {
        'pelicula': pelicula,
        'funciones': funciones,
        'form': form
    })

# ---------------------------
# Checkout y pagos
# ---------------------------

@login_required
def checkout(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    if reserva.estado != "pendiente":
        messages.warning(request, "Esta reserva ya fue procesada.")
        return render(request, "peliculas/checkout.html", {"reserva": reserva})

    try:
        unit_price = float(reserva.funcion.precio)
        if unit_price <= 0:
            raise ValueError("Precio inválido")
    except Exception:
        messages.error(request, "No se pudo iniciar el pago: precio de la función inválido.")
        return render(request, "peliculas/checkout.html", {"reserva": reserva})

    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    preference_data = {
        "items": [{
            "title": f"Entrada {reserva.funcion.pelicula.titulo}",
            "quantity": int(reserva.cantidad),
            "currency_id": "ARS",
            "unit_price": unit_price,
        }],
        "back_urls": {
            "success": request.build_absolute_uri(reverse("pago_exitoso", args=[reserva.id])),
            "failure": request.build_absolute_uri(reverse("pago_fallido", args=[reserva.id])),
        },
        "auto_return": "approved",
        "notification_url": request.build_absolute_uri(reverse("mp_webhook")),
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        resp = preference_response.get("response", {}) or {}
        status = preference_response.get("status")

        logger.info("MP preference create status=%s response=%s", status, resp)

        if status != 201:
            cause = resp.get("cause") or resp.get("message") or "Error desconocido"
            messages.error(request, f"No se pudo crear la preferencia de pago: {cause}")
            return render(request, "peliculas/checkout.html", {"reserva": reserva})

        preference_id = resp.get("id")
        if not preference_id:
            messages.error(request, "La respuesta de MercadoPago no incluyó el ID de preferencia.")
            return render(request, "peliculas/checkout.html", {"reserva": reserva})

        reserva.mp_preference_id = preference_id
        reserva.save(update_fields=["mp_preference_id"])

        return render(request, "peliculas/checkout.html", {
            "reserva": reserva,
            "PUBLIC_KEY": settings.MP_PUBLIC_KEY,
            "preference_id": preference_id,
        })
    except Exception as e:
        logger.exception("Error al crear preferencia MP")
        messages.error(request, f"Ocurrió un error al iniciar el pago: {e}")
        return render(request, "peliculas/checkout.html", {"reserva": reserva})

# ---------------------------
# Pago exitoso / fallido
# ---------------------------

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

@login_required
def pago_exitoso(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    if reserva.estado == "pendiente":
        reserva.estado = "pagada"

        # Generar QR
        qr_data = reserva.generar_qr_data()
        qr_img = qrcode.make(qr_data)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        file_name = f"reserva_{reserva.id}.png"
        reserva.qr_code.save(file_name, File(buffer), save=False)
        reserva.save()
        messages.success(request, "¡Pago confirmado! Tu entrada fue generada con QR.")
    else:
        messages.info(request, "Esta reserva ya fue procesada anteriormente.")

    # Generar entradas si no existen
    if not reserva.entradas.exists():
        for i in range(reserva.cantidad):
            Entrada.objects.create(
                reserva=reserva,
                codigo=generar_codigo(),
                asiento=f"A{i+1}"
            )

    return render(request, "peliculas/pago_exitoso.html", {"reserva": reserva})

@login_required
def pago_fallido(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    if reserva.estado == "pendiente":
        reserva.estado = "cancelada"
        reserva.save()
    messages.error(request, "El pago no se pudo completar. Intenta nuevamente.")
    return render(request, "peliculas/pago_fallido.html", {"reserva": reserva})

# ---------------------------
# Webhook de MercadoPago
# ---------------------------

@csrf_exempt
def mp_webhook(request):
    """
    Recibe notificaciones de MercadoPago.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            payment_id = data.get("data", {}).get("id")

            # Aquí podrías usar el SDK de MP para obtener el detalle del pago:
            # sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            # payment_info = sdk.payment().get(payment_id)
            # status = payment_info["response"]["status"]

            return render(request, "peliculas/mp_webhook.html", {"data": data})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Método no permitido"}, status=405)

# ---------------------------
# Pago con tarjeta (Brick)
# ---------------------------

@csrf_exempt
@require_POST
@login_required
def mp_card_payment(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    body = json.loads(request.body.decode("utf-8"))
    token = body.get("token")
    issuer_id = body.get("issuer_id")
    payment_method_id = body.get("payment_method_id")
    installments = int(body.get("installments", 1))
    payer = body.get("payer", {})

    amount = float(reserva.funcion.precio) * int(reserva.cantidad)

    payment_data = {
        "transaction_amount": amount,
        "token": token,
        "description": f"Entradas {reserva.funcion.pelicula.titulo}",
        "installments": installments,
        "payment_method_id": payment_method_id,
        "issuer_id": issuer_id,
        "payer": {
            "email": payer.get("email"),
            "first_name": payer.get("first_name"),
            "last_name": payer.get("last_name"),
            "identification": {
                "type": payer.get("identification", {}).get("type", "DNI"),
                "number": payer.get("identification", {}).get("number"),
            }
        },
        "capture": True,
    }

    try:
        payment_response = sdk.payment().create(payment_data)
        resp = payment_response.get("response", {})
        status = resp.get("status")
        status_detail = resp.get("status_detail")
        mp_payment_id = str(resp.get("id") or "")

        reserva.mp_payment_id = mp_payment_id
        reserva.mp_status = status
        reserva.mp_status_detail = status_detail
        reserva.payment_method = "credit_card"
        reserva.card_brand = payment_method_id
        reserva.installments = installments
        reserva.total_amount = amount

        if status == "approved":
            reserva.estado = "pagada"
            qr_data = reserva.generar_qr_data()
            qr_img = qrcode.make(qr_data)
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            file_name = f"reserva_{reserva.id}.png"
            reserva.qr_code.save(file_name, File(buffer), save=False)
        elif status in ("pending", "in_process"):
            reserva.estado = "pendiente"
        else:
            reserva.estado = "cancelada"

        reserva.save()
        return JsonResponse({"status": status, "payment_id": mp_payment_id})
    except Exception as e:
        logger.exception("Error en pago con tarjeta MP")
        return JsonResponse({"error": str(e)}, status=400)

# ---------------------------
# Administración
# ---------------------------

@user_passes_test(lambda u: u.is_staff)
def marcar_pagada(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    reserva.estado = "pagada"
    reserva.save(update_fields=["estado"])
    messages.success(request, f"La reserva #{reserva.id} fue marcada como pagada.")
    return redirect("reservas_funcion", pk=reserva.funcion.id)

@user_passes_test(lambda u: u.is_staff)
def reservas_funcion(request, pk):
    funcion = get_object_or_404(Funcion, pk=pk)
    estado = request.GET.get("estado")
    reservas = funcion.reserva_set.all()
    if estado in ["pendiente", "pagada", "cancelada"]:
        reservas = reservas.filter(estado=estado)
    return render(request, "peliculas/reservas_funcion.html", {
        "funcion": funcion,
        "reservas": reservas,
        "estado_actual": estado,
    })

@user_passes_test(lambda u: u.is_staff)
def salas_admin(request):
    salas = Sala.objects.all()
    return render(request, "peliculas/salas_admin.html", {"salas": salas})

@user_passes_test(lambda u: u.is_staff)
def desactivar_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    sala.activa = False
    sala.save(update_fields=["activa"])
    return redirect("salas_admin")

@user_passes_test(lambda u: u.is_staff)
def activar_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    sala.activa = True
    sala.save(update_fields=["activa"])
    return redirect("salas_admin")

# ---------------------------
# Extras
# ---------------------------

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, "Registro exitoso. ¡Bienvenido!")
            return redirect('inicio')
    else:
        form = UserCreationForm()
    return render(request, 'peliculas/signup.html', {'form': form})

def soporte(request):
    return render(request, 'peliculas/soporte.html')

@login_required
def mis_entradas(request):
    reservas = Reserva.objects.filter(usuario=request.user).select_related('funcion__pelicula').order_by('-id')
    return render(request, 'peliculas/mis_entradas.html', {'reservas': reservas})

def clean_precio(self):
    valor = self.cleaned_data.get('precio')
    if isinstance(valor, str):
        valor = valor.replace(',', '.')
    return valor

def pago_tarjeta(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if request.method == "POST":
        metodo = request.POST.get("metodo")
        reserva.estado = "Pagado con " + metodo.capitalize()
        reserva.save()
        return redirect("confirmacion", reserva_id=reserva.id)
