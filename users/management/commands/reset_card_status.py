from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = "Reset business card status to None for cards that are not under review"

    def handle(self, *args, **options):
        # Get all users who have a business card front but status is pending_review
        users_with_cards = User.objects.filter(
            business_card_front__isnull=False, business_card_status="pending_review"
        )

        # Count of users before update
        initial_count = users_with_cards.count()
        self.stdout.write(
            f"Found {initial_count} users with cards in pending_review status"
        )

        # Reset status to None
        for user in users_with_cards:
            user.business_card_status = None
            user.save(update_fields=["business_card_status"])
            self.stdout.write(f"Reset status for user {user.email}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully reset business card status for {initial_count} users"
            )
        )
