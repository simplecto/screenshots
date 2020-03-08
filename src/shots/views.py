import json
from django import forms
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from shots.models import ScreenShot
from django.forms import ModelForm
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt


class ScreenShotForm(ModelForm):
    class Meta:
        model = ScreenShot
        fields = ('url', 'format', )
        widgets = {
            'format' : forms.RadioSelect()
        }

def latest_entry(request):
    return ScreenShot.objects.filter(status=ScreenShot.SUCCESS)\
           .latest("created_at").created_at

@condition(last_modified_func=latest_entry)
@cache_page(60, cache="page")
def index(request):
    form = ScreenShotForm()
    shots = ScreenShot.objects\
                .filter(status=ScreenShot.SUCCESS)\
                .order_by('-created_at').all()[:30]

    data = {
        'form': form,
        'shots': shots
    }
    return render(request, "index.html", data)


def about(request):
    return render(request, "about.html")


@require_http_methods(["POST"])
def screenshot_create(request):
    form = ScreenShotForm(request.POST)

    if form.is_valid():
        shot = form.save()
        return redirect(shot)

    data = {
        'form': form
    }

    return render(request, "index.html", data)


def screenshot_get(request, id):
    shot = get_object_or_404(ScreenShot, id=id)
    data = {
        'shot': shot
    }
    return render(request, "screenshot_get.html", data)


def health_check(request):
    return HttpResponse('OK')

@csrf_exempt
def api_screenshot(request):
    body_unicode = request.body.decode('utf-8')

    try:
        body = json.loads(body_unicode)
    except json.decoder.JSONDecodeError as e:
        data = {
            'message': 'Invalid JSON'
        }
        return JsonResponse(data=data, status=400)

    url = body['url'] if 'url' in body else None
    callback_url = body['callback_url'] if 'callback_url' in body else None
    keywords = body['keywords'] if 'keywords' in body else None
    sleep_seconds = body['sleep_seconds'] if 'sleep_seconds' in body else 5
    dpi = body['dpi'] if 'dpi' in body else 1.0

    if not url:
        data = {
            'message': 'url is a required parameter'
        }
        return JsonResponse(data=data, status=400)

    s = ScreenShot(url=url,
                   callback_url=callback_url,
                   keywords=keywords,
                   sleep_seconds=sleep_seconds,
                   dpi=dpi)

    try:
        s.full_clean()
    except ValidationError as e:
        data = {
            'errors': ','.join(e.messages)
        }
        return JsonResponse(data=data, status=400)

    s.save()
    data = {
        'id': s.id,
        'url': s.url
    }

    if callback_url:
        data['callback_url'] = s.callback_url

    return JsonResponse(data=data, status=201)
