from django.contrib import admin
from django.urls import path
from shots import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('about', views.about, name='about'),
    path('screenshot/create', views.screenshot_create, name='screenshot_create'),
    path('screenshot/<uuid:id>', views.screenshot_get, name='screenshot_get'),
    path('health-check', views.health_check, name='health-check'),
]
