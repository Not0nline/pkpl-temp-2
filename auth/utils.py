import jwt
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser

User = get_user_model()

def generate_jwt(user):
    """Generates a JWT for the given user"""
    payload = {
        'id': str(user.id),
        'full_phone': user.full_phone,
        'role': 'staff' if user.is_staff else 'user',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.JWT_EXPIRATION_SECONDS),
        'iat': datetime.datetime.utcnow()
    }
    print(settings.JWT_SECRET_KEY)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

def decode_jwt(token):
    """Decodes the JWT and returns the user object"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user = CustomUser.objects.get(id=payload['id'])
        return user
    except (jwt.ExpiredSignatureError, jwt.DecodeError, ObjectDoesNotExist):
        return None
