import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import RegexValidator
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings
import base64
import re

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


class CustomUserManager(BaseUserManager):
    def create_user(self, id, phone_number, country_code, card_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        if not country_code:
            raise ValueError('The Country Code field must be set')
        if not card_number or not re.match(r'^\d{16}$', card_number):
            raise ValueError('Card number must be exactly 16 digits.')
        if not password or not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&^#])[A-Za-z\d@$!%*?&^#]{8,}$', password):
            raise ValueError('Password must contain at least 8 characters, 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character')
        
        # Remove leading zero if present
        if phone_number.startswith('0'):
            phone_number = phone_number[1:]
        
        # Format full phone number with country code
        full_phone = f"{country_code}{phone_number}"
        card_number, signature = encrypt_and_sign(card_number)

        user = self.model(
            id = id,
            phone_number=phone_number,
            country_code=country_code,
            full_phone=full_phone,
            card_number=card_number,
            card_signature=signature,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, country_code, card_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, country_code, card_number, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Card numer validator (exactly 16 digits)
    card_validator = RegexValidator(
        regex=r'^\d{16}$',
        message="Card number must be exactly 16 digits."
    )
    
    class Meta:
        app_label = 'auth'
    # Override the related_name for groups and user_permissions
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',
        related_query_name='customuser'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser'
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country_code = models.CharField(max_length=5, default="62")  # e.g., 1, 44, 62
    phone_number = models.CharField(max_length=15)  # Phone number without country code
    full_phone = models.CharField(max_length=20, unique=True, default="")  # Country code + phone number
    card_number = models.CharField(
        max_length=16, 
        validators=[card_validator],
        default="0000000000000000"
    )
    card_signature = models.TextField(default="none")
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'full_phone'
    REQUIRED_FIELDS = ['phone_number', 'country_code', 'card_number']

    objects = CustomUserManager()

    def __str__(self):
        return self.full_phone
    
    @classmethod
    def authenticate(cls, full_phone, password=None):
        try:
            # Check request validity
            if not all([full_phone, password]):
                return 405, "Invalid request parameters"
                       
            # Check if user exists
            try:
                user = cls.objects.get(full_phone=full_phone)
                # Verify password
                if user.check_password(password):
                    return 200, user
                else:
                    return 401, "Invalid password"
            except cls.DoesNotExist:
                return 404, "User not found"
            
        except Exception as e:
            return 500, str(e)
