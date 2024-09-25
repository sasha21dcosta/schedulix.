from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from .forms import  UserRegistrationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_control
from django.shortcuts import get_object_or_404

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            # Ensure the user is registered as a regular user (not admin)
            user.is_staff = False
            user.save()
            messages.success(request, f'Account created for {user.username}')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register_view.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Username OR password is incorrect')

    return render(request, 'login_view.html')

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    if request.user.is_staff:
        greeting = "Hello Admin"
    else:
        greeting = "Hello User"

    context = {'greeting': greeting}
    return render(request, 'home.html', context, )
def start(request):
    return render(request, 'start.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_confirm_view(request):
    if request.method == 'GET':
        confirm = request.GET.get('confirm')
        if confirm == 'yes':
            logout(request)
            return redirect('login')
    return render(request, 'logout_confirm.html')


from django.shortcuts import render, redirect
from .models import AdminTimeSlot, Appointment, Notification

from .forms import AdminTimeSlotForm
from .forms import AppointmentForm

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import AdminTimeSlotForm


@login_required
def add_time_slot(request):
    if request.method == 'POST':
        form = AdminTimeSlotForm(request.POST)
        if form.is_valid():
            time_slot = form.save(commit=False)
            time_slot.admin = request.user
            time_slot.save()
            return redirect('time_slot_list')  # Redirect to time slot list view
    else:
        form = AdminTimeSlotForm()

    return render(request, 'add_time_slot.html', {'form': form})


def time_slot_list(request):
    time_slots = AdminTimeSlot.objects.filter(admin=request.user)
    return render(request, 'time_slot_list.html', {'time_slots': time_slots})


from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AppointmentForm
from .models import AdminTimeSlot, Appointment

@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user  # Assign the logged-in user to the appointment

            # Check if the admin has scheduled any time slots for the given date
            booked_time_slots = AdminTimeSlot.objects.filter(
                admin=appointment.admin,
                date=appointment.appointment_date,
                start_time__lte=appointment.start_time,
                end_time__gte=appointment.end_time,
                is_booked=True
            )

            if booked_time_slots.exists():
                # Time slot is already booked
                messages.error(request, 'The selected time slot is not available. Please try again.')
                return redirect('book_appointment')

            # If no booked time slots conflict, proceed to book the appointment
            appointment.status = 'P'  # Set status to Pending
            appointment.save()

            # Mark the time slot as booked
            AdminTimeSlot.objects.create(
                admin=appointment.admin,
                date=appointment.appointment_date,
                start_time=appointment.start_time,
                end_time=appointment.end_time,
                is_booked=True,
                title=appointment.purpose  # You might want to store appointment purpose or other details
            )

            messages.success(request, 'Your appointment has been booked and is waiting for the admin\'s approval.')
            return redirect('appointment_success')
    else:
        form = AppointmentForm()

    return render(request, 'book_appointment.html', {'form': form})


@login_required
def manage_appointments(request):
    pending_appointments = Appointment.objects.filter(admin=request.user, status='P')
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        action = request.POST.get('action')
        appointment = get_object_or_404(Appointment, id=appointment_id)

        if action == 'accept':
            appointment.status = 'A'
            messages.success(request, 'Appointment accepted.')
            # Create a success notification for the user
            Notification.objects.create(
                user=appointment.user,
                message=f"Your appointment with {appointment.admin.username} on {appointment.appointment_date} at {appointment.start_time} has been accepted. Please be present."
            )

        elif action == 'reject':
            appointment.status = 'R'
            messages.success(request, 'Appointment rejected.')
            # Create a rejection notification for the user
            Notification.objects.create(
                user=appointment.user,
                message=f"Your appointment with {appointment.admin.username} on {appointment.appointment_date} at {appointment.start_time} has been rejected."
            )
        appointment.save()
        # Notify the user (similar to the admin notification method)
        return redirect('manage_appointments')

    return render(request, 'manage_appointments.html', {'appointments': pending_appointments})

def appointment_success(request):
    return render(request, 'appointment_success.html')

def calendar(request):
    return render(request, 'calendar.html')
def recurring_event (request):
    return render(request, 'recurring_event.html')

@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(user=request.user)

    # Mark all unread notifications as read
    user_notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications.html', {'notifications': user_notifications})


