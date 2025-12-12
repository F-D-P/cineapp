from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Pelicula(models.Model):
    titulo = models.CharField(max_length=100)
    director = models.CharField(max_length=100)
    genero = models.CharField(max_length=50, choices=[
        ('accion', 'Acción'),
        ('comedia', 'Comedia'),
        ('drama', 'Drama'),
        ('terror', 'Terror'),
        ('aventura', 'Aventura'),
        ('romance', 'Romance'),
        ('ciencia_ficcion', 'Ciencia Ficción'),
        ('fantasia', 'Fantasía'),
        ('documental', 'Documental'),
        ('musical', 'Musical'),
        ('animacion', 'Animación'),
        ('suspenso', 'Suspenso'),
        ('historica', 'Histórica'),
        ('crimen', 'Crimen'),
        ('misterio', 'Misterio'),
    ])
    
    fecha_estreno = models.DateField()
    sinopsis = models.TextField()
    imagen = models.ImageField(upload_to='peliculas/', blank=True, null=True)
    es_estreno = models.BooleanField(default=False)
    duracion = models.PositiveIntegerField(
    null=True,
    blank=True,
    help_text="Duración en minutos"
    )

    def promedio_puntuacion(self):
        puntuaciones = self.puntuaciones.all()
        if puntuaciones.exists():
            return round(sum(p.valor for p in puntuaciones) / puntuaciones.count(), 1)
        return None

    def __str__(self):
        return self.titulo


class Puntuacion(models.Model):
    pelicula = models.ForeignKey('Pelicula', on_delete=models.CASCADE, related_name='puntuaciones')
    valor = models.IntegerField(choices=[(i, f"{i} estrellas") for i in range(1, 6)])
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pelicula.titulo} - {self.valor} estrellas"


class Funcion(models.Model):
    SALAS = [
        ('Sala 1', 'Sala 1'),
        ('Sala 2', 'Sala 2'),
        ('Sala 3', 'Sala 3'),
        ('Sala 4', 'Sala 4'),
        ('Sala 5', 'Sala 5'),
        ('Sala 6', 'Sala 6'),
    ]

    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='funciones')
    fecha = models.DateField()
    hora = models.TimeField()
    sala = models.CharField(max_length=50, choices=SALAS)  # 👈 ahora con choices
    capacidad = models.PositiveIntegerField(default=100)

    precio = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    FORMATO_CHOICES = [
        ('2D', '2D'),
        ('3D', '3D'),
        ('4D', '4D'),
    ]
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES, default='2D')

    IDIOMA_CHOICES = [
        ('ES', 'Español'),
        ('SUB', 'Subtitulada'),
    ]
    idioma = models.CharField(max_length=10, choices=IDIOMA_CHOICES, default='ES')

    lleno = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.pelicula.titulo} - {self.fecha} {self.hora} - Sala {self.sala}"
class Asiento(models.Model):
    funcion = models.ForeignKey(Funcion, on_delete=models.CASCADE, related_name='asientos')
    fila = models.CharField(max_length=1)  # A, B, C...
    numero = models.IntegerField()         # 1, 2, 3...
    estado = models.CharField(max_length=10, choices=[
        ('libre', 'Libre'),
        ('ocupado', 'Ocupado'),
        ('reservado', 'Reservado'),
    ], default='libre')

    def __str__(self):
        return f"{self.fila}{self.numero} - {self.estado}"


from django.db import models
from django.contrib.auth.models import User

from django.db import models
from django.contrib.auth.models import User

class Reserva(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
        ('validada', 'Validada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    funcion = models.ForeignKey('Funcion', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    asientos = models.ManyToManyField('Asiento', blank=True)  # varios asientos en una sola reserva
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    qr_code = models.ImageField(upload_to='qr/', blank=True, null=True)  # QR generado tras el pago
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Campos extra para integrar con MercadoPago
    mp_payment_id = models.CharField(max_length=100, blank=True, null=True)
    mp_preference_id = models.CharField(max_length=100, blank=True, null=True)

    # Campos de tarjetas
    mp_preference_id = models.CharField(max_length=64, blank=True, null=True)
    mp_payment_id = models.CharField(max_length=64, blank=True, null=True)
    mp_status = models.CharField(max_length=32, blank=True, null=True)          # e.g. approved, pending, rejected
    mp_status_detail = models.CharField(max_length=64, blank=True, null=True)   # e.g. accredited, cc_rejected_other_reason
    payment_method = models.CharField(max_length=32, blank=True, null=True)     # e.g. credit_card
    card_brand = models.CharField(max_length=32, blank=True, null=True)         # e.g. visa, master
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    installments = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.usuario} - {self.funcion.pelicula.titulo} ({self.cantidad})"

    def lista_asientos(self):
        """Devuelve los asientos en formato legible"""
        return ", ".join([str(a) for a in self.asientos.all()])

    def generar_qr_data(self):
        """Datos mínimos que irán en el QR"""
        return f"RESERVA:{self.id}|FUNCION:{self.funcion.id}|ASIENTOS:{self.lista_asientos()}"

    def actualizar_estado_pago(self, status, payment_id=None):
        """Actualiza el estado de la reserva según la respuesta de MercadoPago"""
        if status == "approved":
            self.estado = "pagada"
            self.mp_payment_id = payment_id
        elif status == "rejected":
            self.estado = "cancelada"
        self.save()

class Sala(models.Model):
    nombre = models.CharField(max_length=50)
    capacidad = models.IntegerField()
    activa = models.BooleanField(default=True)  # Para desactivar sin eliminar

    def __str__(self):
        return self.nombre
    
class Entrada(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name="entradas")
    codigo = models.CharField(max_length=12, unique=True)
    asiento = models.CharField(max_length=5)
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Entrada {self.codigo} - {self.reserva.funcion}"
