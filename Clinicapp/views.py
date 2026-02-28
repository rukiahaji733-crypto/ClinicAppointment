from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import Appointment, Doctor, Patient
from .Serializer import AppointmentSerializer, DoctorSerializer

# User Login API - with CSRF exempt for development
@csrf_exempt
@api_view(['POST'])
def api_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {"error": "Please provide username and password"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if user is not None:
        # Log the user in to create a session
        login(request, user)
        return Response(
            {
                "message": "Login successful",
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            },
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

# GET all appointments
@api_view(['GET'])
def api_appointments(request):
    appointments = Appointment.objects.select_related('patient', 'doctor').all()
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)

# POST book appointment
@api_view(['POST'])
def api_book_appointment(request):
    doctor_id = request.data.get('doctor')
    date = request.data.get('date')
    time = request.data.get('time')
    patient_name = request.data.get('name', '')
    patient_phone = request.data.get('phone', '')

    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return Response({"error": "Doctor not found"}, status=404)

    # Get or create patient using the name from the form
    if patient_name:
        # Split name into first_name and last_name
        name_parts = patient_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Try to find existing patient by name
        patient = Patient.objects.filter(first_name__iexact=first_name).first()
        
        if not patient:
            # Create new patient with the entered name
            patient = Patient.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}@patient.com",
                phone=patient_phone or ''
            )
    elif request.user.is_authenticated:
        # Use logged in user data
        patient, _ = Patient.objects.get_or_create(
            user=request.user,
            defaults={
                'first_name': request.user.first_name or 'Unknown',
                'last_name': request.user.last_name or 'Patient',
                'email': request.user.email or 'patient@clinic.com',
                'phone': ''
            }
        )
    else:
        # Fallback
        patient, _ = Patient.objects.get_or_create(
            email='anonymous@clinic.com',
            defaults={
                'first_name': 'Anonymous',
                'last_name': 'Patient',
                'phone': ''
            }
        )

    appointment = Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        date=date,
        time=time
    )

    serializer = AppointmentSerializer(appointment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# DELETE cancel appointment
@api_view(['DELETE'])
def api_cancel_appointment(request, id):
    try:
        appointment = Appointment.objects.get(pk=id)
    except Appointment.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    appointment.delete()
    return Response({"message": "Appointment deleted successfully"})

# GET doctors list
@api_view(['GET'])
def api_doctors(request):
    doctors = Doctor.objects.all()
    serializer = DoctorSerializer(doctors, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_doctor(request):
    serializer = DoctorSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_doctor(request, id):
    try:
        doctor = Doctor.objects.get(id=id)
    except Doctor.DoesNotExist:
        return Response(
            {"error": "Doctor not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    doctor.delete()

    return Response(
        {"message": "Doctor deleted successfully"},
        status=status.HTTP_200_OK
    )

# Dashboard API
@api_view(['GET'])
def api_dashboard(request):
    total_appointments = Appointment.objects.count()
    total_doctors = Doctor.objects.count()
    upcoming_appointments = Appointment.objects.order_by('date', 'time')[:5]

    upcoming_serializer = AppointmentSerializer(upcoming_appointments, many=True)

    data = {
        "total_appointments": total_appointments,
        "total_doctors": total_doctors,
        "upcoming_appointments": upcoming_serializer.data
    }

    return Response(data)

# User Registration API - with CSRF exempt for development
@csrf_exempt
@api_view(['POST'])
def api_register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    # Validation
    if not username or not email or not password:
        return Response(
            {"error": "Please provide username, email and password"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if password != confirm_password:
        return Response(
            {"error": "Passwords do not match"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Email already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    return Response(
        {"message": "User registered successfully", "user_id": user.id},
        status=status.HTTP_201_CREATED
    )

# Register Patient API - with CSRF exempt for development
@csrf_exempt
@api_view(['POST'])
def api_register_patient(request):
    name = request.data.get('name')
    email = request.data.get('email')
    phone = request.data.get('phone')
    
    if not name or not email:
        return Response(
            {"error": "Please provide name and email"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Split name into first_name and last_name
    name_parts = name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Check if patient with this email already exists
    existing_patient = Patient.objects.filter(email=email).first()
    if existing_patient:
        return Response(
            {"message": "Patient already exists", "patient_id": existing_patient.id},
            status=status.HTTP_200_OK
        )
    
    # Create patient
    patient = Patient.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone or ''
    )
    
    return Response(
        {"message": "Patient registered successfully", "patient_id": patient.id},
        status=status.HTTP_201_CREATED
    )
