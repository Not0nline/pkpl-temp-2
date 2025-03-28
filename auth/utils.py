import jwt
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64


User = get_user_model()

def encrypt_and_sign(message):
    # Convert message to bytes
    message_bytes = message.encode('utf-8')

    encrypted_message = settings.RECEIVER_PUBLIC_KEY.encrypt(
        message_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Sign the message with the sender's private key
    signature = settings.SENDER_PRIVATE_KEY.sign(
        encrypted_message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    return base64.b64encode(encrypted_message).decode(), base64.b64encode(signature).decode()

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
