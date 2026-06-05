from django.core.management.base import BaseCommand
import asyncio

from proof_checker.instagram_scraper import save_instagram_session


class Command(BaseCommand):
    help = "Save Instagram login session manually"

    def handle(self, *args, **kwargs):
        asyncio.run(save_instagram_session())