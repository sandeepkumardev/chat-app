from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Room, Message, PrivateRoom
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q

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
        room_name = request.POST.get('room_name')
        if not Room.objects.filter(name=room_name).exists():
            Room.objects.create(name=room_name, created_by=request.user)
            return redirect(f"{reverse('home')}?room={room_name}")
        else:
            messages.error(request, 'Room name already exists')
    return render(request, 'create_room.html')

@login_required
def delete_room(request, room_id):
    next_url = request.GET.get('next') or 'home'
    room = get_object_or_404(Room, id=room_id)

    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Room deleted successfully.')
    return redirect(next_url)

@login_required
def profile(request):
    rooms = Room.objects.filter(created_by=request.user)
    messages = Message.objects.filter(user=request.user).order_by('-timestamp')[:20]
    return render(request, 'profile.html', {'rooms': rooms, 'messages': messages})

@login_required
def home(request):
    storage = messages.get_messages(request)
    list(storage)

    rooms = Room.objects.all()
    users = User.objects.all()

    # private_rooms = PrivateRoom.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    # # Extract users from those private rooms, excluding self
    # users_with_chat_history = []
    # for room in private_rooms:
    #     if room.user1 == request.user:
    #         users_with_chat_history.append(room.user2)
    #     else:
    #         users_with_chat_history.append(room.user1)
    # # Optionally make users unique
    # users_with_chat_history = list(set(users_with_chat_history))

    selected_room = None
    selected_user = None
    private_room = None
    chat_messages = []

    room_name = request.GET.get("room")
    user_name = request.GET.get("chat")
    if room_name:
        try:
            selected_room = Room.objects.get(slug=room_name)
            chat_messages = selected_room.messages.order_by('timestamp')[:50]
        except Room.DoesNotExist:
            messages.error(request, 'Selected room does not exist')
    elif user_name:
        try:
            selected_user = User.objects.get(username=user_name)
            private_room = get_or_create_private_chat(request.user, selected_user)
            chat_messages = private_room.messages.order_by('timestamp')[:50]
        except User.DoesNotExist:
            messages.error(request, 'Selected user does not exist')

    return render(request, 'home.html', {
        'rooms': rooms,
        'users': users,
        'selected_room': selected_room,
        'selected_user': selected_user,
        'private_room': private_room,
        'messages': chat_messages,
        'error_message': messages.get_messages(request)
    })


def get_or_create_private_chat(user1, user2):
    from .models import PrivateRoom

    # Sort to make sure order doesn't matter
    user1, user2 = sorted([user1, user2], key=lambda u: u.id)

    room, created = PrivateRoom.objects.get_or_create(user1=user1, user2=user2)
    return room


def signup_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        username = request.POST['username'].strip()
        password = request.POST['password']

        if not username or not password:
            messages.error(request, "Username and password are required.")
        elif ' ' in username:
            messages.error(request, "Username cannot contain spaces.")
        elif not username.isalnum():
            messages.error(request, "Username can only contain letters and numbers.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            User.objects.create_user(first_name=name, username=username, password=password)
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
    return render(request, 'signup.html')

def login_view(request):
    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        username = request.POST['username'].strip()
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect(request.POST.get('next') or 'home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html', {'next': next_url})

def logout_view(request):
    logout(request)
    return redirect('login')

from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.utils.text import slugify
@csrf_exempt
def create_room_ajax(request):
    if request.method == "POST":
        data = json.loads(request.body)
        name = data.get("name", "").strip()
        if not name:
            return JsonResponse({"success": False, "error": "Room name is required"})

        slug = slugify(name)
        # Check if room with slug exists
        if Room.objects.filter(slug=slug).exists():
            return JsonResponse({"success": False, "error": "Room already exists"})

        # Create new room with logged-in user as creator (adjust if needed)
        room = Room.objects.create(name=name, slug=slug, created_by=request.user)
        return JsonResponse({"success": True, "slug": room.slug})

    return JsonResponse({"success": False, "error": "Invalid request"})