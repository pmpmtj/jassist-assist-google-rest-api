import os
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import logging

class Command(BaseCommand):
    help = 'Fixes Google OAuth configuration by cleaning up the database'

    def handle(self, *args, **options):
        logger = logging.getLogger('jassist_app')
        
        # 1. Delete ALL existing Google social apps
        deleted_count = SocialApp.objects.filter(provider='google').delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count[0]} Google apps'))
        logger.info(f'Deleted {deleted_count[0]} Google apps')
        
        # 2. Get the site
        try:
            site = Site.objects.get(id=2)
            self.stdout.write(f'Using site: {site.domain} (ID: {site.id})')
            logger.info(f'Using site: {site.domain} (ID: {site.id})')
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR('Site with ID 2 does not exist. Creating it...'))
            logger.warning('Site with ID 2 does not exist. Creating it...')
            site = Site.objects.create(id=2, domain='127.0.0.1:8000', name='Local Dev')
        
        # 3. Get credentials from environment
        client_id = os.getenv('GOOGLE_CLIENT_ID', '')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
        
        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR('GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET environment variables not set'))
            logger.error('Missing Google credentials in environment variables')
            return
        
        # 4. Create a new app
        app = SocialApp.objects.create(
            provider='google',
            name='jassist-assist',
            client_id=client_id,
            secret=client_secret
        )
        
        # 5. Associate with site
        app.sites.add(site)
        app.save()
        
        self.stdout.write(self.style.SUCCESS(f'Created new Google app (ID: {app.id}) and associated with site {site.domain}'))
        logger.info(f'Created new Google app (ID: {app.id}) and associated with site {site.domain}')
        
        # 6. Verify setup
        app = SocialApp.objects.filter(provider='google').first()
        if app:
            site_domains = [s.domain for s in app.sites.all()]
            self.stdout.write(self.style.SUCCESS(f'Configuration verified: App ID = {app.id}, Client ID = {app.client_id}'))
            self.stdout.write(self.style.SUCCESS(f'Associated with sites: {", ".join(site_domains)}'))
            logger.info(f'Configuration verified with sites: {", ".join(site_domains)}')
        else:
            self.stdout.write(self.style.ERROR('Failed to create Google app'))
            logger.error('Failed to create Google app') 