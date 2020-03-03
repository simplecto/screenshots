from django.core.exceptions import ValidationError
import socket
from urllib.parse import urlparse


def validate_hostname_dns(value):

    domain = urlparse(value).netloc.split(':')[0]

    if len(domain) == 0:
        raise ValidationError(f"Domain name is required")

    try:
        socket.gethostbyname(domain)
    except socket.gaierror:
        raise ValidationError(f"{value} does not resolve with public DNS.")
