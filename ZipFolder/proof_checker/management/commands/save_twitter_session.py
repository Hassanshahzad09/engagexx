from django.core.management.base import BaseCommand
import asyncio
from proof_checker.twitter_scraper import save_twitter_session


class Command(BaseCommand):
    help = "Save Twitter/X login session using manual Google login"

    def handle(self, *args, **kwargs):
        asyncio.run(save_twitter_session())