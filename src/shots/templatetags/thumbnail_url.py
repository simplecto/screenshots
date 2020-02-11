import base64
import io
from PIL import ImageOps, Image
from django import template
from django.core.cache import cache

register = template.Library()

@register.simple_tag
def thumbnail(shot, width, height):
    thumb = cache.get(shot.id.hex)
    if not thumb:
        with io.BytesIO(shot.image_binary.tobytes()) as buf:
            with Image.open(buf) as image:
                with io.BytesIO() as tbuffer:
                    thumb = ImageOps.fit(image, (width, height), Image.ANTIALIAS, centering=(1.0, 0.0))
                    thumb.save(tbuffer, "JPEG")
                    b64 = base64.b64encode(tbuffer.getvalue()).decode('ascii')
                    thumb = f'data:image/jpg;base64,{b64}'
                    cache.set(shot.id.hex, thumb, 30 * 86400)  # 30 days

    return thumb