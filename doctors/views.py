from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime, timedelta
from .models import DoctorProfile, TimeSlot

# Create your views here.

@login_required(login_url='login_page')
def doctor_dashboard(request):
    """Main doctor dashboard"""
    try:
        doctor = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        # Auto-create doctor profile if it doesn't exist
        doctor = DoctorProfile.objects.create(user=request.user)

    # Get today's and upcoming slots
    today = datetime.now().date()
    slots = TimeSlot.objects.filter(doctor=doctor, date__gte=today).order_by('date', 'start_time')

    context = {
        'doctor': doctor,
        'slots': slots,
        'today': today,
    }
    return render(request, 'doctors_dashboard.html', context)


@login_required(login_url='login_page')
def add_time_slot(request):
    """Add a new time slot"""
    try:
        doctor = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        duration = request.POST.get('duration', 30)

        try:
            # Validate and parse date and times
            slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()

            # Validate that end time is after start time
            if end_time <= start_time:
                messages.error(request, "End time must be after start time!")
                return redirect('doctor_dashboard')

            # Validate that date is in the future
            if slot_date < datetime.now().date():
                messages.error(request, "Cannot create slots for past dates!")
                return redirect('doctor_dashboard')

            # Check for overlapping slots
            overlapping = TimeSlot.objects.filter(
                doctor=doctor,
                date=slot_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            if overlapping.exists():
                messages.error(request, "This time slot overlaps with an existing slot!")
                return redirect('doctor_dashboard')

            # Create the new slot
            TimeSlot.objects.create(
                doctor=doctor,
                date=slot_date,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=int(duration)
            )

            messages.success(request, f"Time slot added successfully for {slot_date}!")
            return redirect('doctor_dashboard')

        except ValueError as e:
            messages.error(request, "Invalid date or time format!")
            return redirect('doctor_dashboard')

    return render(request, 'add_time_slot.html')


@login_required(login_url='login_page')
def edit_time_slot(request, slot_id):
    """Edit an existing time slot"""
    try:
        doctor = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_dashboard')

    slot = get_object_or_404(TimeSlot, id=slot_id, doctor=doctor)

    if request.method == 'POST':
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        duration = request.POST.get('duration', slot.duration_minutes)
        is_available = request.POST.get('is_available') == 'on'

        try:
            slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()

            # Validate that end time is after start time
            if end_time <= start_time:
                messages.error(request, "End time must be after start time!")
                return redirect('edit_time_slot', slot_id=slot_id)

            # Validate that date is in the future
            if slot_date < datetime.now().date():
                messages.error(request, "Cannot set slots for past dates!")
                return redirect('edit_time_slot', slot_id=slot_id)

            # Check for overlapping slots (excluding current slot)
            overlapping = TimeSlot.objects.filter(
                doctor=doctor,
                date=slot_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(id=slot_id)

            if overlapping.exists():
                messages.error(request, "This time slot overlaps with another slot!")
                return redirect('edit_time_slot', slot_id=slot_id)

            # Update the slot
            slot.date = slot_date
            slot.start_time = start_time
            slot.end_time = end_time
            slot.duration_minutes = int(duration)
            slot.is_available = is_available
            slot.save()

            messages.success(request, "Time slot updated successfully!")
            return redirect('doctor_dashboard')

        except ValueError:
            messages.error(request, "Invalid date or time format!")
            return redirect('edit_time_slot', slot_id=slot_id)

    context = {
        'slot': slot,
        'slot_date': slot.date.strftime('%Y-%m-%d'),
        'slot_start_time': slot.start_time.strftime('%H:%M'),
        'slot_end_time': slot.end_time.strftime('%H:%M'),
    }
    return render(request, 'edit_time_slot.html', context)


@login_required(login_url='login_page')
def delete_time_slot(request, slot_id):
    """Delete a time slot"""
    try:
        doctor = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_dashboard')

    slot = get_object_or_404(TimeSlot, id=slot_id, doctor=doctor)

    if request.method == 'POST':
        slot_date = slot.date
        slot.delete()
        messages.success(request, f"Time slot for {slot_date} has been deleted!")
        return redirect('doctor_dashboard')

    context = {'slot': slot}
    return render(request, 'delete_time_slot.html', context)



@login_required(login_url='login_page')
def toggle_availability(request, slot_id):
    """Toggle slot availability"""
    try:
        doctor = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        messages.error(request, 'Doctor profile not found')
        return redirect('doctor_dashboard')

    slot = get_object_or_404(TimeSlot, id=slot_id, doctor=doctor)
    slot.is_available = not slot.is_available
    slot.save()

    status = "available" if slot.is_available else "unavailable"
    messages.success(request, f'Slot is now {status}')
    return redirect('doctor_dashboard')


@login_required(login_url='login_page')
def doctor_profile(request):
    """View and edit doctor profile"""
    try:
        doctor = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        # Create profile if it doesn't exist
        doctor = DoctorProfile.objects.create(user=request.user)

    if request.method == 'POST':
        doctor.specialization = request.POST.get('specialization', doctor.specialization)
        doctor.phone = request.POST.get('phone', doctor.phone)
        doctor.experience_years = request.POST.get('experience_years', doctor.experience_years)
        doctor.bio = request.POST.get('bio', doctor.bio)
        doctor.is_available = request.POST.get('is_available') == 'on'

        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)

        doctor.save()
        request.user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('doctor_profile')

    context = {'doctor': doctor}
    return render(request, 'doctor_profile.html', context)