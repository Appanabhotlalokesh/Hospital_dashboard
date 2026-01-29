from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import re

# Create your views here.
def index(request):
    return render(request, "index.html")


def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        selected_role = request.POST.get("role")  # doctor / patient

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, "login.html", {
                "error": "Invalid credentials"
            })

        # Ensure UserProfile exists
        from hospital_dashboard.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)

        # 🔐 ROLE VALIDATION
        if profile.role != selected_role:
            return render(request, "login.html", {
                "error": f"Role mismatch. User is registered as {profile.role}, but you selected {selected_role}."
            })

        login(request, user)

        # 🎯 ROLE-BASED REDIRECT
        if profile.role == "doctor":
            return redirect('doctor_dashboard')

        if profile.role == "patient":
            return redirect('patient_dashboard')

    return render(request, "login.html")


def signup_page(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get("role")

        # Validate passwords match
        if password != confirm_password:
            return render(request, "signup.html", {
                "error": "Passwords do not match!"
            })

        # Validate password strength
        if len(password) < 8:
            return render(request, "signup.html", {
                "error": "Password must be at least 8 characters long!"
            })

        if not re.search(r'[A-Z]', password):
            return render(request, "signup.html", {
                "error": "Password must contain at least one uppercase letter!"
            })

        if not re.search(r'[0-9]', password):
            return render(request, "signup.html", {
                "error": "Password must contain at least one number!"
            })

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {
                "error": "Username already taken! Choose another."
            })

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {
                "error": "Email already registered!"
            })

        # Create the user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Ensure UserProfile exists and set role
            from hospital_dashboard.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            return render(request, "login.html", {
                "success": f"Account created successfully! Welcome {first_name}. Please login."
            })

        except Exception as e:
            return render(request, "signup.html", {
                "error": f"An error occurred: {str(e)}"
            })

    return render(request, "signup.html")


def logout_page(request):
    """Logout the user"""
    logout(request)
    return redirect('index')
