from django.shortcuts import render, get_object_or_404
from .models import Pelicula, Funcion, Reserva
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .forms import PeliculaForm
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Q
from django.db.models import Avg
from django.shortcuts import render
from django.db.models import Avg
from django.utils import timezone
from .forms import PuntuacionForm
from .models import Pelicula, Puntuacion
from django.contrib.auth.forms import UserCreationForm
from .forms import FuncionForm
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from .models import Reserva, Asiento 
from django.contrib.admin.views.decorators import staff_member_required

# peliculas/views.py
from django.db.models import Q, Avg
from django.utils import timezone
from django.shortcuts import render
from .models import Pelicula
import mercadopago
from django.conf import settings
from django.urls import reverse
import qrcode
from io import BytesIO
from django.core.files import File
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from .models import Reserva
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
from peliculas.models import Sala
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


def inicio(request):
    genero = request.GET.get('genero')
    query = request.GET.get('q')

    generos_validos = [g[0] for g in Pelicula._meta.get_field('genero').choices]

    # Catálogo: películas ya estrenadas/no-estreno (ajusta según tu lógica)
    catalogo = Pelicula.objects.filter(es_estreno=False)

    if genero in generos_validos:
        catalogo = catalogo.filter(genero=genero)

    if query:
        catalogo = catalogo.filter(
            Q(titulo__icontains=query) |
            Q(genero__icontains=query) |
            Q(director__icontains=query)
        )

    # Próximamente: próximas (puedes mantener tu lógica o filtrar por fecha futura)
    proximamente = Pelicula.objects.filter(es_estreno=True).order_by('fecha_estreno')[:5]
    # Si preferís por fecha futura:
    # proximamente = Pelicula.objects.filter(fecha_estreno__gt=timezone.now()).order_by('fecha_estreno')[:5]

    # Top 5 por promedio de puntuación
    top_peliculas = Pelicula.objects.annotate(
        promedio=Avg('puntuaciones__valor')
    ).filter(promedio__isnull=False).order_by('-promedio')[:5]

    if not top_peliculas.exists():
        top_peliculas = catalogo.order_by('-id')[:5]

    return render(request, 'peliculas/inicio.html', {
        'catalogo': catalogo,
        'proximamente': proximamente,
        'top_peliculas': top_peliculas,
        'genero_actual': genero,
        'query': query,
    })


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

def buscar_pelicula(request):
    query = request.GET.get('q', '')
    resultados = Pelicula.objects.filter(
        Q(titulo__icontains=query) |
        Q(genero__icontains=query) |
        Q(director__icontains=query)
    )
    context = {
        'query': query,
        'resultados': resultados,
    }
    return render(request, 'peliculas/buscar.html', context)

top_peliculas = Pelicula.objects.annotate(
    promedio=Avg('puntuaciones__valor')
).filter(promedio__isnull=False).order_by('-promedio')[:5]

def promedio_puntuacion(self):
    puntuaciones = self.puntuaciones.all()
    if puntuaciones.exists():
        return round(sum(p.valor for p in puntuaciones) / puntuaciones.count(), 1)
    return None

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def soporte(request):
    return render(request, 'peliculas/soporte.html')

from .models import Funcion

from .models import Funcion, Reserva

def reservar_entrada(request):
    funciones = Funcion.objects.select_related('pelicula').order_by('fecha', 'hora')

    if request.method == 'POST':
        funcion_id = request.POST.get('funcion')
        cantidad = request.POST.get('cantidad')
        tipo_usuario = request.POST.get('tipo_usuario', 'general')
        funcion = Funcion.objects.get(id=funcion_id)

        Reserva.objects.create(
            usuario=request.user,
            funcion=funcion,
            cantidad=cantidad,
            tipo_usuario=tipo_usuario
        )
        return redirect('mis_entradas')

    return render(request, 'peliculas/reservar_entrada.html', {'funciones': funciones})

def generar_asientos(funcion):
    filas = ['A', 'B', 'C', 'D', 'E', 'F', 'G']  # ✅ Fila G agregada
    asientos_por_fila = 11  # Incluye columna 0
    for fila in filas:
        for numero in range(0, asientos_por_fila):  # ✅ Desde 0 hasta 10
            funcion.asientos.create(fila=fila, numero=numero)

@login_required
def funciones_disponibles(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    funciones = pelicula.funciones.order_by('fecha', 'hora')

    form = None
    if request.user.is_staff:
        if request.method == 'POST':
            form = FuncionForm(request.POST)
            if form.is_valid():
                nueva_funcion = form.save(commit=False)
                nueva_funcion.pelicula = pelicula
                nueva_funcion.save()
                generar_asientos(nueva_funcion)
                return redirect('funciones_disponibles', pk=pelicula.pk)
        else:
            form = FuncionForm()

    return render(request, 'peliculas/funciones_disponibles.html', {
        'pelicula': pelicula,
        'funciones': funciones,
        'form': form
    })

logger = logging.getLogger(__name__)

@staff_member_required
def agregar_funcion(request, pelicula_id):
    pelicula = get_object_or_404(Pelicula, pk=pelicula_id)

    if request.method == 'POST':
        form = FuncionForm(request.POST)
        if form.is_valid():
            nueva_funcion = form.save(commit=False)
            nueva_funcion.pelicula = pelicula
            nueva_funcion.save()
            generar_asientos(nueva_funcion)
            messages.success(request, 'Función creada correctamente.')
            return redirect('funciones_disponibles', pk=pelicula.id)
        else:
            # Log y mensaje para ver el motivo
            logger.warning(f"Errores al crear función: {form.errors.as_json()}")
            messages.error(request, 'Revisa los campos: hay errores de validación.')
    else:
        form = FuncionForm()

    return render(request, 'peliculas/agregar_funcion.html', {
        'pelicula': pelicula,
        'form': form,
    })

def mis_entradas(request):
    reservas = Reserva.objects.filter(usuario=request.user).select_related('funcion__pelicula').order_by('-id')
    return render(request, 'peliculas/mis_entradas.html', {'reservas': reservas})

@login_required
def seleccionar_asientos(request, funcion_id):
    funcion = get_object_or_404(Funcion, id=funcion_id)

    filas = ['A','B','C','D','E','F']       # filas visibles
    columnas = list(range(1, 11))           # 1..10 para cabecera

    # Un solo queryset ordenado por fila y número (como “antes”)
    asientos = (
        Asiento.objects
        .filter(funcion=funcion)
        .order_by('fila', 'numero')
    )

    context = {
        'funcion': funcion,
        'filas': filas,
        'columnas': columnas,
        'asientos': asientos,
    }
    return render(request, 'peliculas/seleccionar_asientos.html', context)

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

        # 👇 Redirige al checkout
        return redirect("checkout", reserva_id=reserva.id)

    # Si no se seleccionaron asientos, volver a la selección
    return redirect("seleccionar_asientos", funcion_id=funcion.id)

@login_required
def funciones_disponibles(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    funciones = pelicula.funciones.order_by('fecha', 'hora')

    form = None
    if request.user.is_staff:
        if request.method == 'POST':
            form = FuncionForm(request.POST)
            if form.is_valid():
                nueva_funcion = form.save(commit=False)
                nueva_funcion.pelicula = pelicula
                nueva_funcion.save()
                generar_asientos(nueva_funcion)
                return redirect('funciones_disponibles', pk=pelicula.pk)
        else:
            form = FuncionForm()

    return render(request, 'peliculas/funciones_disponibles.html', {
        'pelicula': pelicula,
        'funciones': funciones,
        'form': form
    })

@user_passes_test(lambda u: u.is_staff)
def editar_funcion(request, pk):
    funcion = get_object_or_404(Funcion, pk=pk)
    if request.method == 'POST':
        form = FuncionForm(request.POST, instance=funcion)
        if form.is_valid():
            form.save()
            return redirect('funciones_pelicula', pk=funcion.pelicula.pk)
    else:
        form = FuncionForm(instance=funcion)
    return render(request, 'peliculas/editar_funcion.html', {
        'form': form,
        'funcion': funcion
    })

@user_passes_test(lambda u: u.is_staff)
def eliminar_funcion(request, pk):
    funcion = get_object_or_404(Funcion, pk=pk)
    pelicula_id = funcion.pelicula.pk
    funcion.delete()
    messages.success(request, "La función fue eliminada correctamente.")
    return redirect('funciones_pelicula', pk=pelicula_id)

@login_required
def checkout(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    # Validar que la reserva esté pendiente
    if reserva.estado != "pendiente":
        messages.warning(request, "Esta reserva ya fue procesada.")
        return render(request, "peliculas/checkout.html", {"reserva": reserva})

    # Validar que la función tenga precio definido
    try:
        unit_price = float(reserva.funcion.precio)
        if unit_price <= 0:
            raise ValueError("Precio inválido")
    except Exception:
        messages.error(request, "No se pudo iniciar el pago: precio de la función inválido.")
        return render(request, "peliculas/checkout.html", {"reserva": reserva})

    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    preference_data = {
        "items": [
            {
                "title": f"Entrada {reserva.funcion.pelicula.titulo}",
                "quantity": int(reserva.cantidad),
                "currency_id": "ARS",
                "unit_price": unit_price,
            }
        ],
        "back_urls": {
            "success": request.build_absolute_uri(reverse("pago_exitoso", args=[reserva.id])),
            "failure": request.build_absolute_uri(reverse("pago_fallido", args=[reserva.id])),
        },
        "auto_return": "approved",
        "notification_url": request.build_absolute_uri(reverse("mp_webhook")),
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        status = preference_response.get("status")
        resp = preference_response.get("response", {}) or {}

        # Log útil para depurar en consola
        logger.info("MP preference create status=%s response=%s", status, resp)

        if status != 201:
            # MercadoPago responde 201 en creación exitosa
            cause = resp.get("cause") or resp.get("message") or "Error desconocido"
            messages.error(request, f"No se pudo crear la preferencia de pago: {cause}")
            return render(request, "peliculas/checkout.html", {"reserva": reserva})

        preference_id = resp.get("id")
        if not preference_id:
            messages.error(request, "La respuesta de MercadoPago no incluyó el ID de preferencia.")
            return render(request, "peliculas/checkout.html", {"reserva": reserva})

        # Guardar el preference_id en la reserva
        reserva.mp_preference_id = preference_id
        reserva.save(update_fields=["mp_preference_id"])

        return render(
            request,
            "peliculas/checkout.html",
            {
                "reserva": reserva,
                "PUBLIC_KEY": settings.MP_PUBLIC_KEY,
                "preference_id": preference_id,
            },
        )
    except Exception as e:
        logger.exception("Error al crear preferencia MP")
        messages.error(request, f"Ocurrió un error al iniciar el pago: {e}")
        return render(request, "peliculas/checkout.html", {"reserva": reserva})


from .models import Entrada
import random
import string

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

    # 👇 Generar entradas si no existen
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

# Webhook de MercadoPago
from django.http import JsonResponse

def mp_webhook(request):
    """Recibe notificaciones de MercadoPago"""
    if request.method == "POST":
        data = request.POST or request.body
        # Aquí deberías parsear el JSON que envía MP y actualizar la reserva
        # Ejemplo simplificado:
        # reserva = Reserva.objects.get(mp_preference_id=data["data"]["id"])
        # reserva.actualizar_estado_pago(data["status"], data["id"])
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt  # MercadoPago no envía CSRF token
def mp_webhook(request):
    """
    Recibe notificaciones de MercadoPago.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            # Ejemplo de payload simplificado:
            # {
            #   "id": 123456789,
            #   "live_mode": true,
            #   "type": "payment",
            #   "date_created": "...",
            #   "application_id": "...",
            #   "user_id": "...",
            #   "api_version": "v1",
            #   "action": "payment.created",
            #   "data": { "id": "987654321" }
            # }

            # En este punto deberías consultar la API de MP con el payment_id
            payment_id = data.get("data", {}).get("id")

            # Aquí podrías usar el SDK de MP para obtener el detalle del pago:
            # sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            # payment_info = sdk.payment().get(payment_id)
            # status = payment_info["response"]["status"]
            # preference_id = payment_info["response"]["order"]["id"]

            # Para debug, mostramos lo recibido
            return render(request, "peliculas/mp_webhook.html", {"data": data})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

# peliculas/views.py
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import mercadopago

@csrf_exempt
@require_POST
@login_required
def mp_card_payment(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    body = json.loads(request.body.decode("utf-8"))
    token = body.get("token")                    # token del card brick
    issuer_id = body.get("issuer_id")            # emisor (si aplica)
    payment_method_id = body.get("payment_method_id")  # visa, master, etc.
    installments = int(body.get("installments", 1))
    payer = body.get("payer", {})                # name, email, identification

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
        status = resp.get("status")                    # approved | pending | rejected
        status_detail = resp.get("status_detail")
        mp_payment_id = str(resp.get("id") or "")

        # Persistimos detalles
        reserva.mp_payment_id = mp_payment_id
        reserva.mp_status = status
        reserva.mp_status_detail = status_detail
        reserva.payment_method = "credit_card"
        reserva.card_brand = payment_method_id
        reserva.installments = installments
        reserva.total_amount = amount

        # Last4: viene dentro de additional_info si lo setearas; si no, lo omitimos
        # reserva.card_last4 = resp.get("card", {}).get("last_four_digits")

        # Estado interno
        if status == "approved":
            reserva.estado = "pagada"
            # Generar QR (reutilizamos tu lógica)
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

def clean_precio(self):
    valor = self.cleaned_data.get('precio')
    # Si llega como string con coma, normaliza
    if isinstance(valor, str):
        valor = valor.replace(',', '.')
    return valor

from django.shortcuts import render, redirect, get_object_or_404
from .models import Reserva

def pago_tarjeta(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if request.method == "POST":
        metodo = request.POST.get("metodo")
        # Aquí simulas que el pago fue exitoso
        reserva.estado = "Pagado con " + metodo.capitalize()
        reserva.save()
        return redirect("confirmacion", reserva_id=reserva.id)
