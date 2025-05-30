from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = "Change business card status from pending_review to accepted"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit the number of cards to accept (default: all)",
        )
        parser.add_argument(
            "--email",
            type=str,
            help="Accept cards for a specific email only",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )

    def handle(self, *args, **options):
        # Get filters from command options
        limit = options.get("limit")
        email = options.get("email")
        dry_run = options.get("dry_run", False)

        # Build query to find cards in pending review
        query = User.objects.filter(business_card_status="pending_review")
        
        # Filter by email if provided
        if email:
            query = query.filter(email=email)
            self.stdout.write(f"Filtering for email: {email}")
            
        # Ensure they have a business card front
        query = query.filter(business_card_front__isnull=False)
        
        # Apply limit if specified
        if limit:
            query = query[:limit]
            self.stdout.write(f"Limiting to {limit} cards")

        # Count of users before update
        initial_count = query.count()
        self.stdout.write(
            f"Found {initial_count} users with cards in pending_review status"
        )
        
        if initial_count == 0:
            self.stdout.write(self.style.WARNING("No cards found to accept"))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
            for user in query:
                self.stdout.write(f"Would accept card for: {user.email}")
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY RUN - Would accept {initial_count} cards"
                )
            )
            return

        # Change status to accepted
        for user in query:
            user.business_card_status = "accepted"
            user.save(update_fields=["business_card_status"])
            self.stdout.write(f"Accepted card for user: {user.email}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully accepted {initial_count} business cards"
            )
        ) 