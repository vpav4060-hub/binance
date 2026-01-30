from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from datetime import date
from .models import Usuario, Transaccion, Producto, Recarga, CuentaBancaria, Inversion, Retiro, CuentaUsuario, ComisionReferido
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from.forms import ProductoForm, CuentaBancariaForm
from django.contrib import messages
import random
from django.utils import timezone
from datetime import timedelta
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url='login')
def juegos(request):
    juegos = [
    {
        'nombre': 'Ruleta',
    'icono': '🎡',
    'estado': 'Próximamente'
    },
    {
    'nombre': 'Tragamonedas',
    'icono': '🎰',
    'estado': 'Próximamente'
    },  
    {
    'nombre': 'Cartas',
    'icono': '🃏',
    'estado': 'Próximamente'
    },
    {
    'nombre': 'Dados',
    'icono': '🎲',
    'estado': 'Próximamente'
    },
    ]


    return render(request, 'inverso_sa/juegos.html', {
    'juegos': juegos
})