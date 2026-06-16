from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from .decorators import unauthenticated_user
from .forms import CreateUserForm, doctor_infos
from . import models
from .models import doctor_infos, DoctorSchedule

# =========================
# IMPORTS
# =========================
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from datetime import datetime, timedelta  # ✅ here


# =========================
# SLOT GENERATION FUNCTION
# =========================
def generate_slots(start_time, end_time, duration=20):
    slots = []
    current = start_time

    while current < end_time:
        next_time = (
            datetime.combine(datetime.today(), current)
            + timedelta(minutes=duration)
        ).time()

        if next_time > end_time:
            break

        slots.append(current)
        current = next_time

    return slots
# =========================
# HOME PAGE
# =========================
def home(request):

    specialization = request.GET.get('specialization')
    search_query = request.GET.get('q', '')

    doctors = doctor_infos.objects.all()

    if specialization and specialization != "All":
        doctors = doctors.filter(specialist_in=specialization)

    if search_query:
        from django.db.models import Q
        doctors = doctors.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    specializations = doctor_infos.objects.values_list(
        'specialist_in',
        flat=True
    ).distinct()

    context = {
        'doctors': doctors,
        'specializations': specializations,
        'selected_specialization': specialization,
        'search_query': search_query
    }

    return render(request, 'home.html', context)


# =========================
# REGISTER
# =========================
@unauthenticated_user
def register(request):

    form = CreateUserForm()

    if request.method == 'POST':

        form = CreateUserForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email'].lower()

            user.save()

            group = Group.objects.get(name='Patient')
            user.groups.add(group)

            messages.success(
                request,
                f'Account created successfully for {user.first_name} {user.last_name}. Please login.'
            )

            return redirect('login')

        else:
            messages.error(
                request,
                'Please provide valid details.'
            )

    return render(request, 'register.html', {'form': form})
# =========================
# LOGIN WITH EMAIL
@unauthenticated_user
def login_page(request):

    next_url = request.GET.get('next')

    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email__iexact=email)
            username = user_obj.username
        except User.DoesNotExist:
            username = None

        user = authenticate(request, username=username, password=password)

        if user is not None:

            # ✅ LOGIN USER
            login(request, user)

            # 🔥 IMPORTANT: redirect back to original page
            if next_url:
                return redirect(next_url)

            # fallback redirect
            return redirect('to_user_login')

        else:
            messages.error(request, 'Invalid Email or Password')

    return render(request, 'login.html')

# =========================
# LOGOUT
# =========================
@login_required
def logout_user(request):
    logout(request)
    return redirect('home')


# =========================
# ROLE BASED REDIRECT
# =========================
@login_required(login_url='login')
def to_user_login(request):

    user = request.user

    if user.groups.filter(name='Admin').exists():
        return redirect('/admin/')

    if user.groups.filter(name='Doctor').exists():
        return redirect('appointment')

    if user.groups.filter(name='Patient').exists():
        return redirect('patient')

    return redirect('home')


# =========================
# DOCTOR PROFILE PAGE
# =========================
@login_required(login_url='login')
def doctor_front(request):
    return render(request, 'doctor_front.html')


@login_required(login_url='login')
def doctor(request):

    form = doctor_infos()
    user = get_user(request)

    if request.method == 'POST':

        try:
            instance = get_object_or_404(
                models.doctor_infos,
                id=user
            )

            form = doctor_infos(
                request.POST,
                request.FILES,
                instance=instance
            )

        except Exception:
            form = doctor_infos(
                request.POST,
                request.FILES
            )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Doctor profile saved successfully."
            )
            return HttpResponseRedirect('doctor_front')

    else:

        try:
            info = models.doctor_infos.objects.get(id=user)
            form = doctor_infos(instance=info)

        except Exception:

            form = doctor_infos(initial={
                'id': user,
                'email': user.email
            })

    return render(
        request,
        'doctor.html',
        {'form': form}
    )

def doctor_detail(request, id):

    doctor = get_object_or_404(
        models.doctor_infos,
        doctor__id=id
    )

    schedules = models.DoctorSchedule.objects.filter(
        doctor__id=id,
        is_booked=False
    ).order_by('date', 'start_time')

    return render(request, 'doctor_detail.html', {
        'doctor': doctor,
        'schedules': schedules
    })
@login_required(login_url='login')
def patient(request):

    user = request.user
    doctor_id = request.GET.get('doctor')

    selected_doctor = None
    available_slots = []

    if doctor_id and doctor_id != 'None':

        try:
            selected_doctor = User.objects.get(id=doctor_id)

            schedules = DoctorSchedule.objects.filter(
                doctor=selected_doctor,
                is_booked=False
            )

            for schedule in schedules:

                slots = generate_slots(
                    schedule.start_time,
                    schedule.end_time
                )

                for slot in slots:

                    # ✅ prevent double booking
                    already_booked = models.scheduled_appointments.objects.filter(
                        doctor=selected_doctor,
                        date=schedule.date,
                        time=slot
                    ).exists()

                    if not already_booked:
                        available_slots.append({
                            'date': schedule.date,
                            'time': slot
                        })

        except (User.DoesNotExist, ValueError):
            messages.error(request, "Doctor not found.")
            return redirect('home')

    # =========================
    # BOOK APPOINTMENT
    # =========================
    if request.method == 'POST':

        schedule_id = request.POST.get('schedule')
        doctor_id = request.POST.get('doctor_id') or request.GET.get('doctor')

        if not schedule_id:
            messages.error(request, "Please select a slot.")
            return redirect(request.path + f'?doctor={doctor_id}')

        schedule_to_book = models.DoctorSchedule.objects.filter(
            id=schedule_id,
            is_booked=False
        ).first()

        if not schedule_to_book:
            messages.error(request, "Slot already booked or invalid.")
            return redirect(request.path + f'?doctor={doctor_id}')

        doctor = schedule_to_book.doctor

        # Extract priority scheduling fields
        try:
            age = int(request.POST.get('age', 30))
        except (ValueError, TypeError):
            age = 30

        try:
            emergency_level = int(request.POST.get('emergency_level', 1))
            if emergency_level not in (1, 2, 3):
                emergency_level = 1
        except (ValueError, TypeError):
            emergency_level = 1

        mobile_number = request.POST.get('mobile_number')
        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            messages.error(request, "Please enter a valid 10-digit mobile number.")
            return redirect(request.path + f'?doctor={doctor_id}')

        # ✅ save booking
        new_appt = models.scheduled_appointments.objects.create(
            doctor=doctor,
            patient=user.username,
            date=schedule_to_book.date,
            time=schedule_to_book.start_time,
            reason=request.POST.get('reason'),
            symptoms=request.POST.get('symptoms'),
            email_id=user.email,
            mobile_number=mobile_number,
            age=age,
            emergency_level=emergency_level,
        )

        # 🛑 mark the schedule as booked
        schedule_to_book.is_booked = True
        schedule_to_book.save()

        # ✅ redirect to success page with download option
        return redirect('booking_success', appointment_id=new_appt.pk)

    doctors = models.doctor_infos.objects.all()

    return render(request, 'patient.html', {
        'doctor': doctors,
        'selected_doctor': selected_doctor,
        'schedules': schedules if 'schedules' in locals() else []
    })

# =========================
# DOCTOR DASHBOARD
# =========================
@login_required(login_url='login')
def appointment(request):

    if not request.user.groups.filter(
        name='Doctor'
    ).exists():
        return redirect('home')

    user = request.user

    # Fetch all appointments for this doctor
    appointments_qs = models.scheduled_appointments.objects.filter(
        doctor=user
    )

    # Compute real-time priority for each appointment so waiting time
    # is always up-to-date, then sort highest score first.
    scheduled_list = list(appointments_qs)
    for appt in scheduled_list:
        appt.live_priority = appt.calculate_priority()

    scheduled_list.sort(
        key=lambda a: (-a.live_priority, a.booked_at)
    )

    EMERGENCY_LABELS = {1: 'Normal', 2: 'Urgent', 3: 'Critical'}
    for appt in scheduled_list:
        appt.emergency_label = EMERGENCY_LABELS.get(appt.emergency_level, 'Normal')

    return render(
        request,
        'appointment.html',
        {'scheduled': scheduled_list}
    )


# =========================
# DOCTOR SCHEDULE
# =========================
@login_required(login_url='login')
def doctor_schedule(request):

    if not request.user.groups.filter(
        name='Doctor'
    ).exists():
        return redirect('home')

    user = request.user
    from .forms import DoctorScheduleForm

    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = user
            schedule.save()
            messages.success(request, "Schedule added successfully.")
            return redirect('schedule')
    else:
        form = DoctorScheduleForm()

    schedules = models.DoctorSchedule.objects.filter(
        doctor=user
    ).order_by('date', 'start_time')

    return render(
        request,
        'schedule.html',
        {
            'form': form,
            'schedules': schedules
        }
    )


# =========================
# BOOKING SUCCESS PAGE
# =========================
@login_required(login_url='login')
def booking_success(request, appointment_id):
    from django.shortcuts import get_object_or_404
    appt = get_object_or_404(
        models.scheduled_appointments,
        pk=appointment_id,
        patient=request.user.username   # patients can only view their own
    )
    try:
        doctor_info = models.doctor_infos.objects.get(doctor=appt.doctor)
    except models.doctor_infos.DoesNotExist:
        doctor_info = None

    EMERGENCY_LABELS = {1: 'Normal', 2: 'Urgent', 3: 'Critical'}
    appt.emergency_label = EMERGENCY_LABELS.get(appt.emergency_level, 'Normal')
    appt.live_priority = appt.calculate_priority()

    return render(request, 'booking_success.html', {
        'appt': appt,
        'doctor_info': doctor_info,
    })


# =========================
# DOWNLOAD APPOINTMENT PDF
# =========================
@login_required(login_url='login')
def download_appointment_pdf(request, appointment_id):
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    import io
    from django.utils import timezone

    appt = get_object_or_404(
        models.scheduled_appointments,
        pk=appointment_id,
        patient=request.user.username
    )

    try:
        doctor_info = models.doctor_infos.objects.get(doctor=appt.doctor)
        doctor_name    = f"Dr. {doctor_info.first_name} {doctor_info.last_name}"
        doctor_spec    = doctor_info.specialist_in
        clinic_address = f"{doctor_info.address}, {doctor_info.city}, {doctor_info.province}"
    except models.doctor_infos.DoesNotExist:
        doctor_name    = appt.doctor.get_full_name() or appt.doctor.username
        doctor_spec    = "—"
        clinic_address = "—"

    EMERGENCY_LABELS = {1: 'Normal', 2: 'Urgent', 3: 'Critical'}
    EMERGENCY_COLORS = {
        1: colors.HexColor('#27ae60'),
        2: colors.HexColor('#f39c12'),
        3: colors.HexColor('#e74c3c'),
    }
    emergency_label = EMERGENCY_LABELS.get(appt.emergency_level, 'Normal')
    emergency_color = EMERGENCY_COLORS.get(appt.emergency_level, colors.green)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    brand_blue = colors.HexColor('#2c3e50')

    style_title = ParagraphStyle(
        'BrandTitle', parent=styles['Normal'],
        fontSize=22, textColor=colors.white,
        alignment=TA_CENTER, fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    style_subtitle = ParagraphStyle(
        'BrandSub', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor('#bdc3c7'),
        alignment=TA_CENTER, fontName='Helvetica',
    )
    style_body = ParagraphStyle(
        'DetailBody', parent=styles['Normal'],
        fontSize=10, textColor=brand_blue,
        fontName='Helvetica', leading=16,
    )
    style_ref = ParagraphStyle(
        'BookingRef', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#95a5a6'),
        alignment=TA_CENTER, fontName='Helvetica',
    )
    style_footer = ParagraphStyle(
        'PdfFooter', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#95a5a6'),
        alignment=TA_CENTER, fontName='Helvetica',
    )

    elems = []

    # ── Header banner ─────────────────────────────────────
    header_data = [[Paragraph('🏥  Doctor Appointment Booking System', style_title)]]
    header_table = Table(header_data, colWidths=[170 * mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), brand_blue),
        ('TOPPADDING',    (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    elems.append(header_table)

    sub_data = [[Paragraph('Appointment Booking Confirmation', style_subtitle)]]
    sub_table = Table(sub_data, colWidths=[170 * mm])
    sub_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), brand_blue),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    elems.append(sub_table)
    elems.append(Spacer(1, 8 * mm))

    # ── Booking reference ─────────────────────────────────
    elems.append(Paragraph(
        f'Booking Reference: <b>#APT-{appt.pk:05d}</b>', style_ref
    ))
    elems.append(Spacer(1, 4 * mm))
    elems.append(HRFlowable(width='100%', thickness=1,
                             color=colors.HexColor('#e0e0e0')))
    elems.append(Spacer(1, 4 * mm))

    # ── Emergency badge ───────────────────────────────────
    emg_data = [[Paragraph(f'Emergency Level:  <b>{emergency_label}</b>', style_body)]]
    emg_table = Table(emg_data, colWidths=[170 * mm])
    emg_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), emergency_color),
        ('TEXTCOLOR',     (0, 0), (-1, -1), colors.white),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
    ]))
    elems.append(emg_table)
    elems.append(Spacer(1, 6 * mm))

    # ── Details grid ──────────────────────────────────────
    def row(label, value):
        return [
            Paragraph(f'<b>{label}</b>', style_body),
            Paragraph(str(value) if value else '—', style_body),
        ]

    detail_data = [
        row('Patient Name',      f"{request.user.first_name} {request.user.last_name}"),
        row('Patient Age',       f"{appt.age} years"),
        row('Email',             appt.email_id),
        row('Mobile',            appt.mobile_number),
        ['', ''],
        row('Doctor',            doctor_name),
        row('Specialisation',    doctor_spec),
        row('Clinic Address',    clinic_address),
        ['', ''],
        row('Appointment Date',  appt.date.strftime('%A, %d %B %Y')),
        row('Appointment Time',  appt.time.strftime('%I:%M %p')),
        row('Reason for Visit',  appt.reason),
        row('Symptoms',          appt.symptoms or '—'),
        row('Priority Score',    f"{appt.calculate_priority()}"),
        ['', ''],
        row('Booked On',         appt.booked_at.strftime('%d %B %Y, %I:%M %p')),
    ]

    detail_table = Table(detail_data, colWidths=[55 * mm, 115 * mm])
    detail_table.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('LINEBELOW',     (0, 0), (-1, -2), 0.3, colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR',     (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
    ]))
    elems.append(detail_table)

    elems.append(Spacer(1, 8 * mm))
    elems.append(HRFlowable(width='100%', thickness=1,
                             color=colors.HexColor('#e0e0e0')))
    elems.append(Spacer(1, 4 * mm))

    # ── Footer ────────────────────────────────────────────
    generated_at = timezone.now().strftime('%d %B %Y at %I:%M %p')
    elems.append(Paragraph(
        f'Generated on {generated_at}  •  Doctor Appointment Booking System  •  Keep this for your records.',
        style_footer
    ))

    doc.build(elems)
    buffer.seek(0)

    filename = f"appointment_{appt.pk}_{appt.date}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# =========================
# PATIENT DASHBOARD
# =========================
@login_required(login_url='login')
def patient_dashboard(request):
    user = request.user

    if not user.groups.filter(name='Patient').exists():
        return redirect('home')

    appointments = list(
        models.scheduled_appointments.objects.filter(
            patient=user.username
        ).select_related('doctor').order_by('-booked_at')
    )

    EMERGENCY_LABELS = {1: 'Normal', 2: 'Urgent', 3: 'Critical'}

    for appt in appointments:
        appt.live_priority    = appt.calculate_priority()
        appt.emergency_label  = EMERGENCY_LABELS.get(appt.emergency_level, 'Normal')
        try:
            appt.doctor_info = models.doctor_infos.objects.get(doctor=appt.doctor)
        except models.doctor_infos.DoesNotExist:
            appt.doctor_info = None

    return render(request, 'patient_dashboard.html', {
        'appointments': appointments,
    })