import datetime
import uuid
from django.core.management.base import BaseCommand
from auth.models import CustomUser

class Command(BaseCommand):
    help = "Seed the database with initial data"

    def handle(self, *args, **kwargs):
        user_data ={
                "country_code": "+62",
                "phone_number": 81234567890,
                "full_phone": 6281234567890,
                "card_number": "1234567812345678",
                "is_active": True,
                "is_staff": True,
                "date_joined": datetime.datetime.now(),
            }
        
        
        if not CustomUser.objects.filter(full_phone=user_data["full_phone"]).exists():
            user = CustomUser.objects.create(
                id=uuid.uuid4(),
                country_code=user_data["country_code"],
                phone_number=user_data["phone_number"],
                full_phone=user_data["full_phone"],
                card_number=user_data["card_number"],
                is_active=user_data["is_active"],
                is_staff=user_data["is_staff"],
                date_joined=user_data["date_joined"],
            )
            user.set_password("defaultpassword")  # Set default password
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created user {user.full_phone}'))
        else:
            self.stdout.write(self.style.WARNING(f'User {user_data["full_phone"]} already exists'))
