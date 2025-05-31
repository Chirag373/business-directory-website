from django.core.management.base import BaseCommand
from django.core.management import call_command
import subprocess
import os
import sys

class Command(BaseCommand):
    help = 'Sets up the admin panel by collecting static files and starting the development server'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up the admin panel...'))
        
        # Collect static files
        self.stdout.write('Collecting static files...')
        call_command('collectstatic', '--noinput')
        
        # Start the development server
        self.stdout.write(self.style.SUCCESS('Starting development server...'))
        self.stdout.write(self.style.WARNING('Visit http://127.0.0.1:8000/admin/ to access the admin panel'))
        call_command('runserver') 