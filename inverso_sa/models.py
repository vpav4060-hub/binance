from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Usuario(AbstractUser):
    codigo_invitacion = models.CharField(max_length=20, unique=True, blank=True)
    referido_por = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referidos"
    )
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bono_primera_recarga = models.BooleanField(default=False)
    recarga_comision_pagada = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.codigo_invitacion:
            import random
            self.codigo_invitacion = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    ingreso_diario = models.DecimalField(max_digits=10, decimal_places=2)
    limite = models.PositiveIntegerField(default=0)
    duracion = models.CharField(max_length=20)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)


class CuentaBancaria(models.Model):
    banco = models.CharField(max_length=100)
    destinatario = models.CharField(max_length=100)
    numero_cuenta = models.CharField(max_length=50)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.banco} - {self.numero_cuenta}"
    

class Transaccion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    cuenta = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT, null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10)  # ingreso / egreso
    referencia = models.CharField(max_length=50, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)



class CuentaUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    banco = models.CharField(max_length=100)
    titular = models.CharField(max_length=150)
    numero_cuenta = models.CharField(max_length=50)
    fecha = models.DateTimeField(auto_now_add=True)


class Recarga(models.Model):
    ESTADOS = (
        ('revision', 'En revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    )

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    cuenta = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    referencia = models.CharField(max_length=50, unique=True)
    voucher = models.ImageField(upload_to='recargas/')
    estado = models.CharField(max_length=15, choices=ESTADOS, default='revision')
    fecha = models.DateTimeField(auto_now_add=True)
    oculto = models.BooleanField(default=False)  # 👈 NUEVO

    def __str__(self):
        return f"{self.usuario.username} - {self.monto}"


class Inversion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    ultimo_pago = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    ganancia_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    dias_pagados = models.PositiveIntegerField(default=0)
    

    def puede_pagar(self):
        ahora = timezone.now()
        proximo_pago = (self.ultimo_pago or self.fecha_inicio) + timedelta(hours=24)
        return ahora >= proximo_pago

    def pagar(self):
        if not self.puede_pagar():
            return

        ingreso = Decimal(self.producto.ingreso_diario)

        # 💰 sumar al saldo
        self.usuario.saldo += ingreso
        self.usuario.save()

         # 📊 acumular ganancia
        self.ganancia_total += ingreso
        self.dias_pagados += 1

        # 🧾 registrar transacción
        Transaccion.objects.create(
            usuario=self.usuario,
            monto=ingreso,
            tipo='ingreso'
        )

        # ⏱ actualizar fecha
        self.ultimo_pago = timezone.now()
        self.save()

class Retiro(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    cuenta = models.ForeignKey(CuentaUsuario, on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=15, default='pendiente')
    fecha = models.DateTimeField(auto_now_add=True)

class ComisionReferido(models.Model):
    invitador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="comisiones_recibidas"
    )

    referido = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="comisiones_generadas"
    )

    monto_base = models.DecimalField(max_digits=12, decimal_places=2)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=4)
    comision = models.DecimalField(max_digits=12, decimal_places=2)

    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invitador.username} ← {self.referido.username}"

