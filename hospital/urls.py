from django.urls import path
from . import views

urlpatterns = [

    # ==========================
    # PUBLIC PAGES
    # ==========================
    path('', views.home, name='home'),
    path('home', views.home, name='home_page'),

    # ==========================
    # AUTHENTICATION
    # ==========================
    path('register', views.register, name='register'),
    path('login_page', views.login_page, name='login'),
    path('logout', views.logout_user, name='logout'),

    # ==========================
    # ROLE REDIRECT
    # ==========================
    path(
        'to_user_login',
        views.to_user_login,
        name='to_user_login'
    ),

    # ==========================
    # PATIENT MODULE
    # ==========================
    path(
        'patient',
        views.patient,
        name='patient'
    ),

    path(
        'patient/dashboard',
        views.patient_dashboard,
        name='patient_dashboard'
    ),

    # ==========================
    # DOCTOR MODULE
    # ==========================
    path(
        'doctor_front',
        views.doctor_front,
        name='doctor_front'
    ),

    path(
        'doctor',
        views.doctor,
        name='doctor'
    ),

    path('doctor_detail/<int:id>/', views.doctor_detail, name='doctor_detail'),

    path(
        'appointment',
        views.appointment,
        name='appointment'
    ),

    path(
        'schedule',
        views.doctor_schedule,
        name='schedule'
    ),

    # ==========================
    # BOOKING SUCCESS & PDF
    # ==========================
    path(
        'booking/success/<int:appointment_id>/',
        views.booking_success,
        name='booking_success'
    ),
    path(
        'booking/download/<int:appointment_id>/',
        views.download_appointment_pdf,
        name='download_appointment_pdf'
    ),
]