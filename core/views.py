from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Room, Message
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_dashboard(request):
    users = User.objects.all()
    rooms = Room.objects.all()
    messages = Message.objects.order_by('-timestamp')[:50]
    return render(request, 'admin_dashboard.html', {
        'users': users,
        'rooms': rooms,
        'messages': messages
    })

@login_required
def create_room(request):
    if request.method == 'POST':
        room_name = request.POST['room_name']
        if not Room.objects.filter(name=room_name).exists():
            Room.objects.create(name=room_name, created_by=request.user)
            return redirect('room_detail', room_name=room_name)
    return render(request, 'create_room.html')

@login_required
def room_detail(request, room_name):
    room = Room.objects.get(name=room_name)
    messages = room.messages.order_by('timestamp')[:50]
    return render(request, 'room_detail.html', {'room': room, 'messages': messages})

@login_required
def profile(request):
    rooms = Room.objects.filter(created_by=request.user)
    messages = Message.objects.filter(user=request.user).order_by('-timestamp')[:20]
    return render(request, 'profile.html', {'rooms': rooms, 'messages': messages})

def home(request):
    rooms = Room.objects.all()
    return render(request, 'home.html', {'rooms': rooms})

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, password=password)
            return redirect('login')
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')
