import os

from django.core.management.base import BaseCommand
from wrapper.models import Server

class Command(BaseCommand):
    help = 'Creates basic server profiles from env var'

    def handle(self, *args, **options):
        try:
            existing_servers = [server.url for server in Server.objects.all()]

            all_servers = os.getenv('SERVERS').split(',')

            new_servers = [server for server in all_servers if server.split("|")[0] not in existing_servers]

            for server in new_servers:
                url, weight = server.split('|')
                new_server = Server(
                    url=url,
                    weight=weight
                )
                new_server.save()

            self.stdout.write(self.style.SUCCESS('Successfully created servers'))
        except Exception as e:
            raise e
