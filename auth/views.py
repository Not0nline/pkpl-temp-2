import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .utils import generate_jwt
from .models import CustomUser
from .utils import sanitize_input

@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            country_code = sanitize_input(data.get('country_code'))
            card_number = sanitize_input(data.get('card_number'))
            phone_number = sanitize_input(data.get('phone_number'))
            password = data.get('password')
            role = data.get('role', 'user')  # Default role is 'user'

            if not phone_number or not password:
                return JsonResponse({'error': 'Username and password are required'}, status=400)

            user_id = uuid.uuid4()
            if CustomUser.objects.filter(phone_number=phone_number, country_code=country_code).exists():
                return JsonResponse({'error': 'Phone number already taken'}, status=400)

            # Create new user
            is_staff = role == 'staff'
            user_id = uuid.uuid4()
            user = CustomUser.objects.create_user(id=user_id, phone_number=phone_number, password=password, is_staff=is_staff, country_code=country_code, card_number=card_number)

            # Generate JWT token
            token = generate_jwt(user)
            response = JsonResponse({'message': 'User registered successfully', 'role': role})
            response['Authorization'] = f'Bearer {token}'  # Add JWT to header
            return response
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        full_phone = sanitize_input(data.get('full_phone'))
        password = data.get('password')
        
        status_code, result = CustomUser.authenticate(full_phone=full_phone, password=password)
        print(status_code, result, full_phone, password)
        
        if status_code == 200:  # Success status code
            token = generate_jwt(result)  # Here result is the user object
            response = JsonResponse({
                'message': 'Login successful', 
                'role': 'staff' if result.is_staff else 'user', 
                'Authorization': f'Bearer {token}'
            })
            return response
        else:
            # Handle different error cases based on status_code if needed
            return JsonResponse({'error': result}, status=status_code)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def protected_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    return JsonResponse({'message': f'Welcome, {request.user.full_phone}! Your role is {"user" if not request.user.is_staff else "staff" }'})

@csrf_exempt
def staff_only_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied. Staff only'}, status=403)

    return JsonResponse({'message': 'Welcome, Staff!'})

@csrf_exempt
def get_credit_card(request):
    if request.user.is_authenticated:
        return JsonResponse({'credit_card': request.user.card_number, 'signature': request.user.card_signature}, status=200)
    
    return JsonResponse({'error': 'Authentication required'}, status=401)
