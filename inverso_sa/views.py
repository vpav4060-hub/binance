from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
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
from django.db.models import Q
# --------------------
# LOGIN
# --------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'inverso_sa/login.html', {
                'error': 'Usuario o contraseña incorrectos'
            })

    return render(request, 'inverso_sa/login.html')


# --------------------
# DASHBOARD
# --------------------
@login_required(login_url='login')
def dashboard(request):

    inversiones = Inversion.objects.filter(
        usuario=request.user,
        activa=True
    )

    for inversion in inversiones:
        inversion.pagar()

    return redirect('inicio')



# --------------------
# LOGOUT
# --------------------
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# --------------------
# REGISTRO
# --------------------

def registro_view(request):

    # -------------------------------
    # 1️⃣ Capturar código de referido
    # -------------------------------
    ref = request.GET.get('ref')
    if ref:
        request.session['ref_codigo'] = ref

    # --------------------------------------
    # 2️⃣ Cerrar sesión si ya está logueado
    # --------------------------------------
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Se cerró tu sesión para registrarte como nuevo usuario.")

    # --------------------------------------
    # 3️⃣ Obtener invitador
    # --------------------------------------
    invitador = None
    codigo = request.session.get('ref_codigo')

    if codigo:
        try:
            invitador = Usuario.objects.get(codigo_invitacion=codigo)
        except Usuario.DoesNotExist:
            invitador = None

    # --------------------------------------
    # 4️⃣ Procesar formulario
    # --------------------------------------
    if request.method == 'POST':

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')  # 📱 teléfono
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # ❌ Contraseñas
        if password1 != password2:
            return render(request, 'inverso_sa/registro.html', {
                'error': 'Las contraseñas no coinciden',
                'invitador': invitador
            })

        # ❌ Teléfono duplicado
        if Usuario.objects.filter(username=username).exists():
            return render(request, 'inverso_sa/registro.html', {
                'error': 'Este número de teléfono ya está registrado',
                'invitador': invitador
            })

        # ❌ Email duplicado
        if Usuario.objects.filter(email=email).exists():
            return render(request, 'inverso_sa/registro.html', {
                'error': 'El correo ya está registrado',
                'invitador': invitador
            })

        # ✅ Crear usuario
        usuario = Usuario.objects.create(
            username=username,   # 📱 teléfono
            email=email,
            first_name=first_name,
            last_name=last_name,
            saldo=20,
            password=make_password(password1)
        )

        # 👥 Grupo
        grupo, _ = Group.objects.get_or_create(name='inversionista')
        usuario.groups.add(grupo)

        # 🔗 Referido
        if invitador:
            usuario.referido_por = invitador
            usuario.save()
            del request.session['ref_codigo']

        messages.success(request, "Registro exitoso. Ahora puedes iniciar sesión.")
        return redirect('login')

    # --------------------------------------
    # 5️⃣ GET
    # --------------------------------------
    return render(request, 'inverso_sa/registro.html', {
        'invitador': invitador
    })
# --------------------
# OTRAS VISTAS
# --------------------
@login_required
def ingreso(request):
    usuario = request.user

    inversiones_activas = Inversion.objects.filter(
        usuario=usuario,
        activa=True
    )

    inversiones_expiradas = Inversion.objects.filter(
        usuario=usuario,
        activa=False
    )

    context = {
        'saldo': usuario.saldo,
        'inversiones_activas': inversiones_activas,
        'inversiones_expiradas': inversiones_expiradas,
        'total_proyectos': inversiones_activas.count(),  # ✅ AQUÍ
    }

    return render(request, 'inverso_sa/ingreso.html', context)

# --------------------
# MIO
# --------------------
@login_required
def mio_view(request):
    usuario = request.user

    inversiones = Inversion.objects.filter(
        usuario=usuario,
        activa=True
    )

    hoy = timezone.now().date()

    ganancias_hoy = Transaccion.objects.filter(
        usuario=usuario,
        tipo='ingreso',
        fecha__date=hoy
    ).aggregate(total=Sum('monto'))['total'] or 0

    context = {
        'usuario': usuario,
        'saldo': usuario.saldo,
        'ganancias_hoy': ganancias_hoy,
        'inversiones': inversiones
    }

    return render(request, 'inverso_sa/mio.html', context)



@staff_member_required
def panel_view(request):

    # 🔐 EJECUTA PAGOS SOLO CUANDO ENTRA EL ADMIN
    inversiones = Inversion.objects.filter(activa=True)
    for inversion in inversiones:
        inversion.pagar()

    # =========================
    # PANEL DE USUARIOS
    # =========================
    filtro = request.GET.get("rol")
    buscar = request.GET.get("buscar")

    usuarios = Usuario.objects.all()

    # FILTRO POR ROL
    if filtro == "admin":
        usuarios = usuarios.filter(is_staff=True)
    elif filtro == "user":
        usuarios = usuarios.filter(is_staff=False)

    # 🔍 BUSCADOR
    if buscar:
        usuarios = usuarios.filter(
            Q(username__icontains=buscar) |
            Q(first_name__icontains=buscar) |
            Q(last_name__icontains=buscar) |
            Q(email__icontains=buscar)
        )

    return render(request, 'inverso_sa/usuarios.html', {
        'usuarios': usuarios,
        'filtro': filtro,
        'buscar': buscar
    })



@login_required
def inicio(request):

    productos = Producto.objects.filter(activo=True)

    return render(request, "inverso_sa/inicio.html", {
        "productos": productos
    })




@login_required
def agregar_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('inicio')  # Redirige a la lista de productos
    else:
        form = ProductoForm()
    return render(request, 'inverso_sa/agregar_producto.html', {'form': form})

from decimal import Decimal, InvalidOperation

@login_required
def recargar_view(request):

    montos_rapidos = [400, 600, 800, 1000, 1500, 3000, 5000]

    cuentas = CuentaBancaria.objects.filter(activa=True)

    if not cuentas.exists():
        messages.error(request, "No hay cuentas bancarias disponibles")
        return redirect("inicio")

    cuenta = random.choice(list(cuentas))

    if request.method == "POST":
        try:
            monto = Decimal(request.POST.get("monto"))
        except (InvalidOperation, TypeError):
            messages.error(request, "Monto inválido")
            return redirect("recargar")

        referencia = request.POST.get("referencia")
        voucher = request.FILES.get("voucher")

        # ✅ VALIDACIÓN MÍNIMA
        if monto < 400:
            messages.error(request, "⚠ El monto mínimo de recarga es C$400")
            return redirect("recargar")

        # ❌ referencia repetida
        if Recarga.objects.filter(referencia=referencia).exists():
            messages.error(request, "Número de referencia repetido")
            return redirect("recargar")

        # ❌ voucher obligatorio
        if not voucher:
            messages.error(request, "Debe adjuntar el comprobante")
            return redirect("recargar")

        Recarga.objects.create(
            usuario=request.user,
            cuenta=cuenta,
            monto=monto,
            referencia=referencia,
            voucher=voucher
        )

        messages.success(request, "✅ Recarga enviada correctamente")
        return redirect("mis_recargas")

    return render(request, "inverso_sa/recargar.html", {
        "cuenta": cuenta,
        "montos_rapidos": montos_rapidos
    })


@login_required
def mis_recargas_view(request):
    recargas = Recarga.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'inverso_sa/mis_recargas.html', {'recargas': recargas})

@login_required
def cuentas_bancarias(request):
    cuentas = CuentaBancaria.objects.all().order_by('-fecha_creacion')
    return render(request, 'inverso_sa/cuentas_bancarias.html', {
        'cuentas': cuentas
    })


@login_required
def crear_cuenta_bancaria(request):
    if request.method == 'POST':
        form = CuentaBancariaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Cuenta bancaria agregada correctamente')
            return redirect('cuentas_bancarias')
    else:
        form = CuentaBancariaForm()

    return render(request, 'inverso_sa/cuenta_form.html', {
        'form': form,
        'titulo': 'Agregar Cuenta Bancaria'
    })


@login_required
def editar_cuenta_bancaria(request, id):
    cuenta = get_object_or_404(CuentaBancaria, id=id)

    if request.method == 'POST':
        form = CuentaBancariaForm(request.POST, instance=cuenta)
        if form.is_valid():
            form.save()
            messages.success(request, '✏ Cuenta bancaria actualizada')
            return redirect('cuentas_bancarias')
    else:
        form = CuentaBancariaForm(instance=cuenta)

    return render(request, 'inverso_sa/cuenta_form.html', {
        'form': form,
        'titulo': 'Editar Cuenta Bancaria'
    })


@login_required
def eliminar_cuenta_bancaria(request, id):
    cuenta = get_object_or_404(CuentaBancaria, id=id)

    cuenta.activa = False
    cuenta.save()

    messages.warning(
        request,
        "⛔ Cuenta bancaria desactivada (no se puede eliminar porque tiene movimientos)"
    )

    return redirect('cuentas_bancarias')


@login_required
def solicitudes_recarga(request):
    """
    Vista para listar todas las solicitudes de recarga en revisión.
    Permite aprobar o rechazar cada recarga mediante POST desde el template.
    """
    recargas = Recarga.objects.filter(estado='revision').order_by('-fecha')

    if request.method == 'POST':
        recarga_id = request.POST.get('recarga_id')
        accion = request.POST.get('accion')  # 'aprobar' o 'rechazar'

        recarga = get_object_or_404(Recarga, id=recarga_id)

        if recarga.estado != 'revision':
            messages.warning(request, '⚠ Esta recarga ya fue procesada.')
            return redirect('solicitudes_recarga')

        if accion == 'aprobar':
            recarga.estado = 'aprobada'
            # Sumar el monto al saldo del usuario
            recarga.usuario.saldo += recarga.monto
            recarga.usuario.save()
            recarga.save()
            messages.success(request, f'✅ Recarga de {recarga.usuario.username} aprobada correctamente.')
        elif accion == 'rechazar':
            recarga.estado = 'rechazada'
            recarga.save()
            messages.warning(request, f'❌ Recarga de {recarga.usuario.username} rechazada.')
        else:
            messages.error(request, 'Acción no válida.')

        return redirect('solicitudes_recarga')

    context = {
        'recargas': recargas,
    }
    return render(request, 'inverso_sa/solicitudes_recarga.html', context)

@login_required
def aprobar_rechazar_recarga(request, id):

    recarga = get_object_or_404(Recarga, id=id)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if recarga.estado != 'revision':
            messages.warning(request, "Esta recarga ya fue procesada")
            return redirect('solicitudes_recarga')

        usuario = recarga.usuario

        if accion == "aprobar":

            # =========================
            # APROBAR RECARGA
            # =========================
            recarga.estado = 'aprobada'
            recarga.save()

            usuario.saldo += recarga.monto
            usuario.save()

            # =========================
            # COMISIÓN SOLO PRIMERA RECARGA
            # =========================
            if usuario.referido_por and not usuario.recarga_comision_pagada:

                invitador = usuario.referido_por
                porcentaje = Decimal("7.7")
                comision = (recarga.monto * porcentaje) / 100

                # 💰 pagar comisión
                invitador.saldo += comision
                invitador.save()

                # ✅ REGISTRAR HISTORIAL (ESTO ES LO QUE FALTABA)
                ComisionReferido.objects.create(
                    invitador=invitador,
                    referido=usuario,
                    monto_base=recarga.monto,
                    porcentaje=porcentaje,
                    comision=comision
                )

                # 🔒 bloquear segunda comisión
                usuario.recarga_comision_pagada = True
                usuario.save()

                messages.success(
                    request,
                    f"🎉 Comisión C$ {comision:.2f} pagada al invitador"
                )

            messages.success(request, "✅ Recarga aprobada correctamente")

        elif accion == "rechazar":
            recarga.estado = 'rechazada'
            recarga.save()
            messages.warning(request, "❌ Recarga rechazada")

    return redirect('solicitudes_recarga')




@login_required
def invertir_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    usuario = request.user

    # ❌ saldo insuficiente
    if usuario.saldo < producto.precio:
        messages.error(request, "❌ Saldo insuficiente")
        return redirect('recargar')

    # ❌ límite alcanzado
    inversiones_actuales = Inversion.objects.filter(
        producto=producto,
        activa=True
    ).count()

    if inversiones_actuales >= producto.limite:
        messages.error(request, "⚠ Producto agotado")
        return redirect('inicio')

    # ✅ descontar saldo
    usuario.saldo -= producto.precio
    usuario.save()

    # ✅ crear inversión
    Inversion.objects.create(
        usuario=usuario,
        producto=producto
    )

    messages.success(request, "✅ Inversión realizada correctamente")
    return redirect('ingreso')


@login_required
def ver_productos(request):
    productos = Producto.objects.all().order_by('-creado')
    return render(request, 'inverso_sa/ver_productos.html', {
        'productos': productos
    })

@login_required
def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)

    if request.method == "POST":
        form = ProductoForm(
            request.POST,
            request.FILES,     # 🔥 ESTO ES LA CLAVE
            instance=producto
        )

        if form.is_valid():
            form.save()
            return redirect('ver_productos')

    else:
        form = ProductoForm(instance=producto)

    return render(request, 'inverso_sa/editar_producto.html', {
        'form': form,
        'producto': producto
    })


@login_required
def toggle_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.activo = not producto.activo
    producto.save()

    if producto.activo:
        messages.success(request, "✅ Producto activado")
    else:
        messages.warning(request, "⛔ Producto desactivado")

    return redirect('ver_productos')

@login_required
def agregar_cuenta_usuario(request):

    if request.method == "POST":
        banco = request.POST.get("banco")
        titular = request.POST.get("titular")
        numero_cuenta = request.POST.get("numero_cuenta")

        if not banco or not titular or not numero_cuenta:
            messages.error(request, "Todos los campos son obligatorios")
            return redirect("agregar_cuenta_usuario")

        if CuentaUsuario.objects.filter(
            usuario=request.user,
            numero_cuenta=numero_cuenta
        ).exists():
            messages.warning(request, "Esta cuenta ya fue registrada")
            return redirect("agregar_cuenta_usuario")

        CuentaUsuario.objects.create(
            usuario=request.user,
            banco=banco,
            titular=titular,
            numero_cuenta=numero_cuenta
        )

        messages.success(request, "Cuenta bancaria agregada correctamente")
        return redirect("inicio")

    return render(request, "inverso_sa/agregar_cuenta_usuario.html")


from decimal import Decimal

@login_required
def retirar_view(request):

    usuario = request.user
    cuentas = CuentaUsuario.objects.filter(usuario=usuario)

    if not cuentas.exists():
        messages.warning(request, "Primero debes agregar una cuenta bancaria")
        return redirect("agregar_cuenta_usuario")

    # SOLO bloquear cuando intenta enviar
    if request.method == "POST":

        if Retiro.objects.filter(usuario=usuario, estado='pendiente').exists():
            messages.warning(request, "Ya tienes un retiro pendiente.")
            return redirect("retirar")

        try:
            monto = Decimal(request.POST.get("monto"))
        except:
            messages.error(request, "Monto inválido")
            return redirect("retirar")

        if monto <= Decimal("300"):
            messages.error(request, "El monto debe ser mayor a C$300")
            return redirect("retirar")

        if monto > usuario.saldo:
            messages.error(request, "Saldo insuficiente")
            return redirect("retirar")

        cuenta = get_object_or_404(
            CuentaUsuario,
            id=request.POST.get("cuenta"),
            usuario=usuario
        )

        comision = monto * Decimal("0.06")
        monto_final = monto - comision

        usuario.saldo -= monto
        usuario.save()

        retiro = Retiro.objects.create(
            usuario=usuario,
            cuenta=cuenta,
            monto=monto,
            comision=comision,
            monto_a_pagar=monto_final,
            estado="pendiente"
        )

        Transaccion.objects.create(
            usuario=usuario,
            monto=monto,
            tipo="egreso",
            referencia=f"RETIRO-{retiro.id}"
        )

        messages.success(
            request,
            f"✅ Retiro enviado. Comisión 6%: C${comision:.2f}. "
            f"Recibirás C${monto_final:.2f}"
        )

        return redirect("historial_retiros")

    # 👇 AHORA SÍ ENTRA AQUÍ
    return render(request, "inverso_sa/retirar.html", {
        "cuentas": cuentas,
        "saldo": usuario.saldo
    })


@login_required
def solicitudes_retiro(request):
    retiros = Retiro.objects.filter(estado="pendiente").order_by("-fecha")
    return render(request, 'inverso_sa/solicitudes_retiro.html', {
        'retiros': retiros
    })


@login_required
def procesar_retiro(request, id):
    retiro = get_object_or_404(Retiro, id=id)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if retiro.estado != "pendiente":
            messages.warning(request, "Este retiro ya fue procesado")
            return redirect("solicitudes_retiro")

        if accion == "aprobar":
            retiro.estado = "aprobado"
            retiro.save()
            messages.success(request, "✅ Retiro aprobado correctamente")

        elif accion == "rechazar":
            retiro.estado = "rechazado"

            retiro.usuario.saldo += retiro.monto
            retiro.usuario.save()
            retiro.save()

            messages.warning(request, "❌ Retiro rechazado y dinero devuelto")

    return redirect("solicitudes_retiro")


@login_required
def equipo_view(request):
    usuario = request.user

    equipo = (
        ComisionReferido.objects
        .filter(invitador=usuario)
        .values("referido__username")
        .annotate(
            total_invertido=Sum("monto_base"),
            total_comision=Sum("comision")
        )
        .order_by("-total_comision")
    )

    link = f"https://inverso1sa-5.onrender.com/registro/?ref={usuario.codigo_invitacion}"

    return render(request, "inverso_sa/equipo.html", {
        "codigo": usuario.codigo_invitacion,
        "link": link,
        "equipo": equipo
    })

@login_required
def toggle_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    usuario.is_active = not usuario.is_active
    usuario.save()

    return redirect("panel_usuarios")

@login_required
def modificar_saldo(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    if request.method == "POST":
        accion = request.POST.get("accion")
        monto = Decimal(request.POST.get("monto"))

        if monto <= 0:
            messages.error(request, "Monto inválido")
            return redirect("panel_usuarios")

        if accion == "sumar":
            usuario.saldo += monto
        elif accion == "restar":
            if usuario.saldo < monto:
                messages.error(request, "Saldo insuficiente")
                return redirect("panel_usuarios")
            usuario.saldo -= monto

        usuario.save()
        messages.success(request, "Saldo actualizado correctamente")

    return redirect("panel_usuarios")


def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    inversiones = Inversion.objects.filter(usuario=usuario)
    recargas = Recarga.objects.filter(usuario=usuario).order_by('-fecha')

    if request.method == "POST":
        usuario.first_name = request.POST.get("first_name")
        usuario.last_name = request.POST.get("last_name")
        usuario.email = request.POST.get("email")
        usuario.username = request.POST.get("username")
        usuario.saldo = Decimal(request.POST.get("saldo"))
        usuario.save()

        messages.success(request, "Usuario actualizado correctamente")
        return redirect("panel_usuarios")

    return render(request, "inverso_sa/editar_usuario.html", {
        "usuario": usuario,
        "inversiones": inversiones,
        "recargas": recargas
    })




@login_required
def eliminar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    if request.user.id == usuario.id:
        messages.error(request, "❌ No puedes eliminar tu propio usuario")
        return redirect("panel_usuarios")

    if request.method == "POST":
        usuario.delete()
        messages.success(request, "🗑 Usuario eliminado correctamente")
        return redirect("panel_usuarios")

    return render(request, "inverso_sa/confirmar_eliminar.html", {
        "usuario": usuario
    })


@login_required
def desactivar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    # evitar auto-eliminarse
    if usuario == request.user:
        return redirect('panel_usuarios')

    usuario.is_active = False
    usuario.save()

    return redirect('panel_usuarios')

@login_required
def activar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    usuario.is_active = True
    usuario.save()

    return redirect('panel_usuarios')


@login_required
def ingresos_egresos(request):

    hoy = timezone.now().date()
    filtro = request.GET.get('filtro', 'dia')

    # =========================
    # BASE (NO ocultas)
    # =========================

    recargas = Recarga.objects.filter(
        estado='aprobada',
        oculto=False
    )

    retiros = Retiro.objects.filter(
        estado='aprobado'
    )

    # =========================
    # FILTRO FECHA
    # =========================

    if filtro == 'dia':
        recargas = recargas.filter(fecha__date=hoy)
        retiros = retiros.filter(fecha__date=hoy)

    elif filtro == 'semana':
        desde = hoy - timedelta(days=7)
        recargas = recargas.filter(fecha__date__gte=desde)
        retiros = retiros.filter(fecha__date__gte=desde)

    elif filtro == 'mes':
        recargas = recargas.filter(
            fecha__year=hoy.year,
            fecha__month=hoy.month
        )
        retiros = retiros.filter(
            fecha__year=hoy.year,
            fecha__month=hoy.month
        )

    # =========================
    # TOTALES
    # =========================

    total_ingresos = recargas.aggregate(
        total=Sum('monto')
    )['total'] or 0

    total_egresos = retiros.aggregate(
        total=Sum('monto')
    )['total'] or 0

    balance = total_ingresos - total_egresos

    # =========================
    # TABLA UNIFICADA
    # =========================

    movimientos = []

    for r in recargas:
        movimientos.append({
            'id': r.id,
            'fecha': r.fecha,
            'usuario': r.usuario.username,
            'detalle': f"Recarga ({r.cuenta.banco})",
            'referencia': r.referencia,
            'tipo': 'ingreso',
            'monto': r.monto
        })

    for r in retiros:
        movimientos.append({
            'fecha': r.fecha,
            'usuario': r.usuario.username,
            'detalle': f"Retiro ({r.cuenta.banco})",
            'referencia': r.cuenta.numero_cuenta,
            'tipo': 'egreso',
            'monto': r.monto
        })

    movimientos = sorted(
        movimientos,
        key=lambda x: x['fecha'],
        reverse=True
    )

    return render(request, 'inverso_sa/ingresos_egresos.html', {
        'movimientos': movimientos,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance': balance,
        'filtro': filtro
    })

@login_required
def ocultar_recarga(request, recarga_id):
    recarga = get_object_or_404(Recarga, id=recarga_id)
    recarga.oculto = True
    recarga.save()
    return redirect('ingresos_egresos')




@login_required
def acerca_de(request):
    return render(request, "inverso_sa/acerca_de.html")


@login_required
def asistencia(request):
    return render(request, "inverso_sa/asistencia.html")

@login_required
def historial_retiros(request):
    retiros = Retiro.objects.filter(usuario=request.user).order_by('-fecha')

    return render(request, 'inverso_sa/historial_retiros.html', {
        'retiros': retiros
    })


def custom_404_view(request, exception):
    # No redirige al login; deja que la URL de registro funcione normalmente
    return render(request, "inverso_sa/404.html", status=404)


def es_admin(user):
    return user.is_superuser or user.groups.filter(name='ADMIN').exists()




