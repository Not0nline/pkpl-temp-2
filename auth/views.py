import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from .utils import generate_jwt
from .models import CustomUser 

# Set up logging for debugging
logger = logging.getLogger(__name__)

@csrf_exempt
def register_view(request):
    logger.info("Register view called with method: %s", request.method)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug("Received registration data: %s", data)
            nama = data.get('nama')
            country_code = data.get('country_code')
            card_number = data.get('card_number')
            phone_number = data.get('phone_number')
            password = data.get('password')
            role = data.get('role', 'user')  # Default role is 'user'
            
            logger.debug("Processing registration: country_code=%s, phone=%s, role=%s", 
                        country_code, phone_number, role)

            if not phone_number or not password:
                logger.warning("Registration failed: Missing required fields")
                return JsonResponse({'error': 'Username and password are required'}, status=400)

            user_id = uuid.uuid4()
            logger.debug("Generated user ID: %s", user_id)
            
            # Check if user exists - Note: This logic might have an issue
            if CustomUser.objects.filter(phone_number=phone_number, country_code=country_code).exists():
                logger.warning("Registration failed: Phone number already exists")
                return JsonResponse({'error': 'Phone number already taken'}, status=400)

            # Create new user
            is_staff = role == 'staff'
            user_id = uuid.uuid4()  # Note: Generating a new UUID, overriding the previous one
            logger.debug("Creating user with ID: %s, is_staff=%s", user_id, is_staff)
            
            user = CustomUser.objects.create_user(
                id=user_id, 
                nama=nama,
                phone_number=phone_number, 
                password=password, 
                is_staff=is_staff, 
                country_code=country_code, 
                card_number=card_number
            )
            logger.info("User created successfully: %s", user.id)

            # Generate JWT token
            token = generate_jwt(user)
            logger.debug("JWT token generated for user: %s", user.id)
            
            response = JsonResponse({'message': 'User registered successfully', 'role': role})
            response['Authorization'] = f'Bearer {token}'  # Add JWT to header
            return response
        
        except json.JSONDecodeError:
            logger.error("Registration failed: Invalid JSON in request body")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.exception("Unexpected error during registration: %s", str(e))
            return JsonResponse({'error': 'Server error during registration'}, status=500)

    logger.warning("Registration failed: Invalid HTTP method %s", request.method)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def login_view(request):
    logger.info("Login view called with method: %s", request.method)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug("Received login data: %s", data)
            
            full_phone = data.get('full_phone')
            password = data.get('password')
            
            logger.debug("Attempting authentication for: %s", full_phone)
            status_code, result = CustomUser.authenticate(full_phone=full_phone, password=password)
            logger.debug("Authentication result: status=%s, result=%s", status_code, 
                        "Success" if status_code == 200 else result)
            
            if status_code == 200:  # Success status code
                token = generate_jwt(result)  # Here result is the user object
                logger.info("Login successful for user: %s", result.id)
                
                response = JsonResponse({
                    'message': 'Login successful', 
                    'role': 'staff' if result.is_staff else 'user', 
                    'Authorization': f'Bearer {token}'
                })
                logger.debug("Response prepared: %s", response.content)
                return response
            else:
                # Handle different error cases based on status_code if needed
                logger.warning("Login failed: %s (status: %s)", result, status_code)
                return JsonResponse({'error': result}, status=status_code)
        except json.JSONDecodeError:
            logger.error("Login failed: Invalid JSON in request body")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.exception("Unexpected error during login: %s", str(e))
            return JsonResponse({'error': 'Server error during login'}, status=500)
    
    logger.warning("Login failed: Invalid HTTP method %s", request.method)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def protected_view(request):
    logger.info("Protected view accessed by user: %s (authenticated: %s)", 
               getattr(request.user, 'id', 'Anonymous'), 
               getattr(request.user, 'is_authenticated', False))
    
    if not request.user.is_authenticated:
        logger.warning("Access denied: Authentication required")
        return JsonResponse({'error': 'Authentication required'}, status=401)

    logger.info("Protected view access granted to user: %s", request.user.id)
    return JsonResponse({'message': f'Welcome, {request.user.full_phone}! Your role is {"user" if not request.user.is_staff else "staff" }'})

@csrf_exempt
def staff_only_view(request):
    logger.info("Staff-only view accessed by user: %s (authenticated: %s, is_staff: %s)", 
               getattr(request.user, 'id', 'Anonymous'), 
               getattr(request.user, 'is_authenticated', False),
               getattr(request.user, 'is_staff', False))
    
    if not request.user.is_authenticated:
        logger.warning("Access denied: Authentication required")
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if not request.user.is_staff:
        logger.warning("Access denied: Staff permission required for user %s", request.user.id)
        return JsonResponse({'error': 'Access denied. Staff only'}, status=403)

    logger.info("Staff-only view access granted to staff user: %s", request.user.id)
    return JsonResponse({'message': 'Welcome, Staff!'})