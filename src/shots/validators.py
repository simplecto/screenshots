from django.core.exceptions import ValidationError
import socket
from urllib.parse import urlparse


def validate_hostname_dns(value):

    domain = urlparse(value).netloc.split(':')[0]

    try:
        socket.gethostbyname(domain)
    except socket.gaierror:
        raise ValidationError(f"{value} is not resolve with public DNS.")
