import base64
from datetime import datetime

from django.contrib.postgres.fields import JSONField
from django.db import models
import uuid
from django.utils.safestring import mark_safe
from django.conf import settings
from django.core import validators
from shots.validators import validate_hostname_dns


class ScreenShot(models.Model):

    NEW = 'N'
    PENDING = 'P'
    SUCCESS = 'S'
    FAILURE = 'F'
    RETRY_1 = 'R1'
    RETRY_2 = 'R2'
    RETRY_3 = 'R3'
    STATUS_CHOICES = (
        (NEW, 'New'),
        (PENDING, 'Pending'),
        (SUCCESS, 'Success'),
        (FAILURE, 'Failed'),
        (RETRY_1, 'Retry #1'),
        (RETRY_2, 'Retry #2'),
        (RETRY_3, 'Retry #3'),
    )

    DESKTOP = 'D'
    MOBILE = 'M'
    FORMAT_CHOICES = (
        (DESKTOP, 'Desktop'),
        (MOBILE, 'Mobile'),
    )

    BROWSER = 'B'
    API = 'A'
    CREATED_WITH_CHOICES = (
        (API, 'API'),
        (BROWSER, 'Browser')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=500, validators=[validators.URLValidator(), validate_hostname_dns ])
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=NEW)
    width = models.IntegerField(default=1366)
    height = models.IntegerField(default=768)
    keywords = models.CharField(blank=True, null=True, max_length=250)
    duration = models.IntegerField(null=True, blank=True)
    image_binary = models.BinaryField(blank=True, null=True)
    format = models.CharField(max_length=1, choices=FORMAT_CHOICES, default=DESKTOP)
    created_at = models.DateTimeField(auto_now_add=True)
    created_with = models.CharField(max_length=1, choices=CREATED_WITH_CHOICES, default=BROWSER)
    callback_url = models.URLField(null=True, blank=True, max_length=500,
                                   validators=[validators.URLValidator(), validate_hostname_dns ])
    sleep_seconds = models.IntegerField(default=5)
    dpi = models.DecimalField(default=1.0, decimal_places=1, max_digits=2)
    meta = JSONField(null=True, blank=True)

    def image_tag(self):
        if self.status == self.SUCCESS:
            return mark_safe(f'<a target="new" href="{self.image_url}">{self.image_thumb()}</a>')
        else:
            return ''

    @property
    def resolution(self):
        return f"{self.width}x{self.height}"

    @property
    def full_data_uri(self):
        #b64 = base64.b64encode(self.image_binary).decode('ascii')
        return f'data:image/jpg;base64,{self.image_as_base64}'

    def get_absolute_url(self):
        return f"/screenshot/{self.id}"

    @property
    def thumb_tag(self):
        # return mark_safe(f'<img src="{self.thumb_data_uri}" alt="Thumbnail"/>')
        return mark_safe(f'<img src="{self.thumb_data_uri}" alt="Thumbnail"/>')

    @property
    def full_tag(self):
        return mark_safe(f'<img src="{self.full_data_uri}" alt="Thumbnail"/>')

    @property
    def image_as_base64(self):
        return base64.b64encode(self.image_binary).decode('ascii')

    image_tag.short_description = 'Image'
