from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from decimal import Decimal
import random
from .models import  Ruleta, Tragamonedas



# ===============================
# 🎮 ZONA DE JUEGOS
# ===============================
@login_required(login_url='login')
def juegos(request):

    juegos = [
        {
            'nombre': 'Ruleta',
            'icono': '🎡',
            'estado': 'Disponible'
        },
        {
            'nombre': 'Tragamonedas',
            'icono': '🎰',
            'estado': 'Disponible'
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

@login_required
def ruleta_view(request):
    return render(request, 'inverso_sa/ruleta.html')


# ===============================
# 🎰 RULETA CASINO
# ===============================
@login_required
def jugar_ruleta(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"})

    from decimal import Decimal
    import random

    monto = Decimal(request.POST.get("monto", 0))
    usuario = request.user

    if monto <= 0:
        return JsonResponse({"error": "Monto inválido"})

    if usuario.saldo < monto:
        return JsonResponse({"error": "Saldo insuficiente"})

    probabilidad_ganar = 20  # 20% gana el jugador
    numero = random.randint(1, 100)

    # Definir multiplicador según el monto
    if monto <= 100:
        multiplicador = Decimal("1.0")  # jugador recibe su apuesta completa
    else:
        multiplicador = Decimal("0.5")  # jugador recibe 50% de su apuesta

    if numero <= probabilidad_ganar:
        ganancia = monto * multiplicador
        usuario.saldo += ganancia
        resultado = "GANÓ"
    else:
        usuario.saldo -= monto
        ganancia = -monto
        resultado = "PERDIÓ"

    usuario.save()

    Ruleta.objects.create(
        usuario=usuario,
        apuesta=monto,
        resultado=resultado,
        ganancia=ganancia
    )

    return JsonResponse({
        "resultado": resultado,
        "ganancia": float(ganancia),
        "saldo": float(usuario.saldo)
    })


@login_required
def tragamonedas_view(request):
    """Página del tragamonedas VIP"""
    simbolos_posibles = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎"]
    return render(request, "inverso_sa/tragamonedas.html", {"symbols": simbolos_posibles})




@login_required
def jugar_tragamonedas(request):
    """Lógica del tragamonedas con probabilidades ajustadas"""
    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"})

    try:
        monto = Decimal(request.POST.get("monto", 0))
    except:
        return JsonResponse({"error": "Monto inválido"})

    usuario = request.user

    if monto <= 0:
        return JsonResponse({"error": "Monto inválido"})
    if usuario.saldo < monto:
        return JsonResponse({"error": "Saldo insuficiente"})

    # -----------------------------
    # PROBABILIDADES según monto
    # -----------------------------
    if monto > 100:
        pesos = [10, 90]  # [Jugador gana, Casa gana]
    else:
        pesos = [20, 80]

    resultado = random.choices(
        ["GANO", "PERDIO"],
        weights=pesos,
        k=1
    )[0]

    # -----------------------------
    # Ganancia / Pérdida
    # -----------------------------
    if resultado == "GANO":
        ganancia = monto * Decimal("1.2")
        usuario.saldo += ganancia
    else:
        ganancia = -monto
        usuario.saldo -= monto

    usuario.save()

    # -----------------------------
    # Símbolos según resultado
    # -----------------------------
    simbolos_posibles = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎"]

    if resultado == "GANO":
        # 3 símbolos iguales
        simbolo_ganador = random.choice(simbolos_posibles)
        simbolos = f"{simbolo_ganador} {simbolo_ganador} {simbolo_ganador}"
    else:
        # 3 símbolos aleatorios que no sean todos iguales
        simbolos_list = random.sample(simbolos_posibles, 3)
        while len(set(simbolos_list)) == 1:
            simbolos_list = random.sample(simbolos_posibles, 3)
        simbolos = " ".join(simbolos_list)

    # -----------------------------
    # Guardar historial
    # -----------------------------
    Tragamonedas.objects.create(
        usuario=usuario,
        apuesta=monto,
        resultado=resultado,
        ganancia=ganancia,
        simbolos=simbolos
    )

    # -----------------------------
    # Respuesta JSON
    # -----------------------------
    return JsonResponse({
        "resultado": resultado,
        "ganancia": float(ganancia),
        "saldo": float(usuario.saldo),
        "simbolos": simbolos
    })

def error_403(request, exception=None):
    """
    Vista personalizada para manejar errores 403
    """
    return render(request, "inverso_sa/forbidden.html", {
        "mensaje": "⚠️ Por favor presiona el botón de ingresar solo una vez y espera mientras el sistema carga."
    })