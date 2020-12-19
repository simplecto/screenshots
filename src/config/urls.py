from django.contrib import admin
from django.urls import path
from shots import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('about', views.about, name='about'),
    path('screenshot/create', views.screenshot_create, name='screenshot_create'),
    path('screenshot/<uuid:id>', views.screenshot_get, name='screenshot_get'),

    path('api/screenshot', views.api_screenshot, name='api-screenshot'),
    path('health-check', views.health_check, name='health-check'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

