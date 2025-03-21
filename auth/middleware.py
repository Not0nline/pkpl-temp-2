from django.http import JsonResponse
from .utils import decode_jwt

class JWTAuthenticationMiddleware:
    """Middleware to authenticate users via JWT stored in the Authorization header."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]  # Extract token after 'Bearer'
            user = decode_jwt(token)
            
            if user:
                request.user = user  # Set the user in request
            else:
                return JsonResponse({'error': 'Invalid or expired token'}, status=401)

        return self.get_response(request)
