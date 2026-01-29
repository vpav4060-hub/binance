from django.urls import path
from . import views

urlpatterns = [


    path("usuarios/toggle/<int:id>/", views.toggle_usuario, name="toggle_usuario"),
    path('usuarios/editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path("usuarios/eliminar/<int:id>/", views.eliminar_usuario, name="eliminar_usuario"),
    path('usuarios/desactivar/<int:id>/', views.desactivar_usuario, name='desactivar_usuario'),
    path('usuarios/activar/<int:id>/', views.activar_usuario, name='activar_usuario'),

    # 🔐 AUTH
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    # 🏠 DASHBOARD
    path('dashboard/', views.dashboard, name='dashboard'),

    # 👤 USUARIO
    path('inicio/', views.inicio, name='inicio'),
    path('mio/', views.mio_view, name='mio'),
    path('ingreso/', views.ingreso, name='ingreso'),
    path('equipo/', views.equipo_view, name='equipo'),

    # 💰 RECARGAS
    path('recargar/', views.recargar_view, name='recargar'),
    path('mis-recargas/', views.mis_recargas_view, name='mis_recargas'),
    path(
    'panel/recargas/procesar/<int:id>/',
    views.aprobar_rechazar_recarga,
    name='aprobar_rechazar_recarga'
),

    # 💸 RETIROS
    path('retirar/', views.retirar_view, name='retirar'),

    # 🏦 CUENTA BANCARIA USUARIO
    path(
        'mi-cuenta-bancaria/',
        views.agregar_cuenta_usuario,
        name='agregar_cuenta_usuario'
    ),

    # 📈 INVERTIR PRODUCTO
    path(
        'invertir/<int:id>/',
        views.invertir_producto,
        name='invertir_producto'
    ),

    # 🧠 PANEL ADMIN
    path('panel/usuarios/', views.panel_view, name='panel_usuarios'),
    path('panel/recargas/', views.solicitudes_recarga, name='solicitudes_recarga'),
    path('panel/retiros/', views.solicitudes_retiro, name='solicitudes_retiro'),

    path(
        'panel/retiros/procesar/<int:id>/',
        views.procesar_retiro,
        name='procesar_retiro'
    ),

    # 📦 PRODUCTOS
    path('productos/', views.ver_productos, name='ver_productos'),
    path('productos/agregar/', views.agregar_producto, name='agregar_producto'),
    path('productos/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('productos/toggle/<int:id>/', views.toggle_producto, name='toggle_producto'),

    # 🏦 CUENTAS SISTEMA
    path('cuentas/bancarias/', views.cuentas_bancarias, name='cuentas_bancarias'),
    path('cuentas/bancarias/nueva/', views.crear_cuenta_bancaria, name='crear_cuenta_bancaria'),
    path('cuentas/bancarias/editar/<int:id>/', views.editar_cuenta_bancaria, name='editar_cuenta_bancaria'),
    path('cuentas/bancarias/eliminar/<int:id>/', views.eliminar_cuenta_bancaria, name='eliminar_cuenta_bancaria'),

    path('finanzas/', views.ingresos_egresos, name='ingresos_egresos'),

path("acerca/", views.acerca_de, name="acerca_de"),
path("asistencia/", views.asistencia, name="asistencia"),

]
