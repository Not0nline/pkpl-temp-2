from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
import json
from .utils import generate_jwt
from django.contrib.auth.models import User
from django.http import JsonResponse
from .utils import generate_jwt


@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            role = data.get('role', 'user')  # Default role is 'user'

            if not username or not password:
                return JsonResponse({'error': 'Username and password are required'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already taken'}, status=400)

            # Create new user
            is_staff = role == 'staff'
            user = User.objects.create_user(username=username, password=password, is_staff=is_staff)
            
            # Generate JWT token
            token = generate_jwt(user)
            response = JsonResponse({'message': 'User registered successfully', 'role': role})
            response['Authorization'] = f'Bearer {token}'  # Add JWT to header
            return response
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            token = generate_jwt(user)
            response = JsonResponse({'message': 'Login successful', 'role': 'staff' if user.is_staff else 'user', 'Authorization':f'Bearer {token}'})
            return response
        return JsonResponse({'error': 'Invalid credentials'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def protected_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    return JsonResponse({'message': f'Welcome, {request.user.username}! Your role is {"user" if not request.user.is_staff else "staff" }'})

@csrf_exempt
def staff_only_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied. Staff only'}, status=403)

    return JsonResponse({'message': 'Welcome, Staff!'})
