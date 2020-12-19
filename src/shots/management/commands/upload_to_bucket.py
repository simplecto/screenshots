import glob
from time import sleep
from pathlib import Path
import boto3
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import sys
import signal

# https://www.simplecto.com/using-django-and-boto3-with-scaleway-object-storage/

class Command(BaseCommand):
    help = 'Watch a folder and move all files into an Object Storage (S3) bucket'

    def handle(self, *args, **options):

        signal.signal(signal.SIGTERM, self.handle_sigterm)
        self.s3 = boto3.client('s3',
                          region_name=settings.AWS_S3_REGION_NAME,
                          endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                          )

        self.stdout.write(self.style.SUCCESS(f'Watching folder for new images...'))

        try:
            while True:
                for f in glob.glob(f"{settings.MEDIA_ROOT}/*.jpg"):
                    self.upload_file(f, delete_after=True)
                sleep(3)

        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS(f'Killed from the keyboard with CTRL-C'))
            self.stdout.write(self.style.SUCCESS(f'Shutting down.'))
            sys.exit()

    def upload_file(self, filename:str, delete_after: bool = False):
        with open(filename, "rb") as f:
            self.stdout.write(self.style.SUCCESS(f'Uploading {filename}...'))
            self.s3.put_object(
                Body=f,
                Bucket=f"{settings.AWS_STORAGE_BUCKET_NAME}",
                Key=Path(filename).name,
                ACL='public-read',
                CacheControl='max-age=31556926'  # 1 year
            )
        if delete_after:
            Path(filename).unlink(missing_ok=True)
        self.stdout.write(self.style.SUCCESS(f'Done.'))

    def handle_sigterm(self):
        self.stdout.write(self.style.SUCCESS(f'Received SIGTERM. Shutting down.'))