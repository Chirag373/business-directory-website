import logging
from django.core.management.base import BaseCommand
from handyman.tasks import match_handyman_services

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Match handyman services with consumer interests and send promotional emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the command without sending actual emails',
        )
        parser.add_argument(
            '--force-match',
            action='store_true',
            help='Force matching regardless of notification preferences',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run the task asynchronously with Celery',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force_match = options.get('force_match', False)
        async_mode = options.get('async', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no emails will be sent'))
        
        if force_match:
            self.stdout.write(self.style.WARNING('Force-match mode - ignoring notification preferences'))
        
        if async_mode:
            self.stdout.write(self.style.WARNING('Running in async mode - task will be processed by Celery workers'))
            # Submit as an async task
            task = match_handyman_services.delay(force_match=force_match, dry_run=dry_run)
            self.stdout.write(self.style.SUCCESS(f'Task submitted to Celery (task_id: {task.id})'))
            self.stdout.write(self.style.WARNING('To check task status, run: celery -A business_directory worker --loglevel=info'))
        else:
            # Run synchronously
            self.stdout.write(self.style.WARNING('Running in synchronous mode - this may take a while'))
            stats = match_handyman_services(force_match=force_match, dry_run=dry_run)
            
            # Print final statistics
            self.stdout.write(self.style.SUCCESS(f'Completed matching process'))
            self.stdout.write(f'Total matches found: {stats["total_matches"]}')
            self.stdout.write(f'Unique consumers matched: {stats["consumers_matched"]}')
            self.stdout.write(f'Promotions that found matches: {stats["promotions_matched"]}')
            self.stdout.write(f'Skipped (no business card): {stats["skipped_no_business_card"]}')
            self.stdout.write(f'Skipped (no description): {stats["skipped_no_description"]}')
            self.stdout.write(f'Skipped (notification preference): {stats["skipped_notification_pref"]}')
            self.stdout.write(f'Skipped (already notified): {stats["skipped_already_notified"]}')
            
            if not dry_run:
                self.stdout.write(self.style.SUCCESS(f'Total emails sent: {stats["total_emails"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Dry run - {stats["total_emails"]} emails would have been sent')) 