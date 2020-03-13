from django.contrib import admin
from .models import ScreenShot


def reset_status(modeladmin, request, queryset):
    queryset.update(status=ScreenShot.NEW)

def reset_status_to_failed(modeladmin, request, queryset):
    queryset.update(status=ScreenShot.FAILURE)

reset_status.short_description = "Reset status to NEW (Refresh Images)"
reset_status_to_failed.short_description = "Mark all as failed"

class ScreenShotAdmin(admin.ModelAdmin):
    list_display = ('url', 'status', 'format', 'keywords', 'created_at')
    list_filter = ('status', 'format', )
    search_fields = ('url', 'keywords',)
    readonly_fields = ('width', 'height', 'duration', 'format', )

    actions = [reset_status, reset_status_to_failed]


admin.site.register(ScreenShot, ScreenShotAdmin)
