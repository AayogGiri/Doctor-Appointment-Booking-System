from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import DateInput, TimeInput

from .models import patient_info, doctor_infos, DoctorSchedule


# =========================
# USER REGISTRATION FORM
# =========================
class CreateUserForm(UserCreationForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'pattern': '[A-Za-z ]+', 'title': 'First name must contain only letters'})
        self.fields['last_name'].widget.attrs.update({'pattern': '[A-Za-z ]+', 'title': 'Last name must contain only letters'})

    # ✅ Email validation
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already exists.")

        return email

    # ✅ Name validation (no garbage like 123abc)
    def clean_first_name(self):
        name = self.cleaned_data.get('first_name')
        if not name.isalpha():
            raise forms.ValidationError("First name must contain only letters.")
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name')
        if not name.isalpha():
            raise forms.ValidationError("Last name must contain only letters.")
        return name
# =========================
# PATIENT FORM
# =========================
class patient_infoForm(ModelForm):

    class Meta:
        model = patient_info

        # system sets these automatically
        exclude = ('status', 'doctor', 'user_name', 'email_id')

        fields = '__all__'

        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'mobile_number': 'Mobile Number',
            'address': 'Address',
            'province': 'Province',
            'city': 'City',
            'sex': 'Sex',
            'dob': 'Date of Birth',
            'reason': 'Reason for Visit',
            'symptoms': 'Symptoms',
            'current_medication_list': 'Current Medication',
            'emergency_first_name': 'Emergency Contact First Name',
            'emergency_last_name': 'Emergency Contact Last Name',
            'emergency_relationship': 'Relationship',
            'emergency_mobile_number': 'Emergency Contact Number',
        }

        widgets = {
            'dob': DateInput(attrs={'type': 'date'}),
            'first_name': forms.TextInput(attrs={'pattern': '[A-Za-z ]+', 'title': 'First name must contain only letters'}),
            'last_name': forms.TextInput(attrs={'pattern': '[A-Za-z ]+', 'title': 'Last name must contain only letters'}),
            'mobile_number': forms.TextInput(attrs={'pattern': '[0-9]{10}', 'title': 'Please enter a valid 10-digit mobile number'}),
            'emergency_first_name': forms.TextInput(attrs={'pattern': '[A-Za-z ]+', 'title': 'First name must contain only letters'}),
            'emergency_last_name': forms.TextInput(attrs={'pattern': '[A-Za-z ]+', 'title': 'Last name must contain only letters'}),
            'emergency_mobile_number': forms.TextInput(attrs={'pattern': '[0-9]{10}', 'title': 'Please enter a valid 10-digit mobile number'}),
        }


# =========================
# DOCTOR PROFILE FORM
# =========================
class doctor_infosForm(ModelForm):

    class Meta:
        model = doctor_infos

        exclude = ('doctor',)

        fields = '__all__'

        labels = {
            'email': 'Email',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'mobile_number': 'Mobile Number',
            'address': 'Address',
            'province': 'Province',
            'city': 'City',
            'sex': 'Sex',
            'specialist_in': 'Specialization',
        }

        widgets = {
            'email': forms.EmailInput(),
            'first_name': forms.TextInput(attrs={'pattern': '[A-Za-z ]+', 'title': 'First name must contain only letters'}),
            'last_name': forms.TextInput(attrs={'pattern': '[A-Za-z ]+', 'title': 'Last name must contain only letters'}),
            'mobile_number': forms.TextInput(attrs={'pattern': '[0-9]{10}', 'title': 'Please enter a valid 10-digit mobile number'}),
        }


# =========================
# DOCTOR SCHEDULE FORM (NEW)
# =========================
class DoctorScheduleForm(ModelForm):

    class Meta:
        model = DoctorSchedule
        fields = ['date', 'start_time', 'end_time']

        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
            'start_time': TimeInput(attrs={'type': 'time'}),
            'end_time': TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import date
        self.fields['date'].widget.attrs['min'] = date.today().strftime('%Y-%m-%d')
        
    def clean_date(self):
        date_val = self.cleaned_data.get('date')
        from datetime import date as dt_date
        if date_val and date_val < dt_date.today():
            raise forms.ValidationError("Schedule date cannot be set before the current date.")
        return date_val