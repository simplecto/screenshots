from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from shots.models import ScreenShot
from django.forms import ModelForm
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition


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
