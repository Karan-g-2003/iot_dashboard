from django.contrib import admin
from .models import Device, Telemetry

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'relay_state', 'temp_threshold_high', 'temp_threshold_low', 'auto_mode', 'last_seen')
    search_fields = ('device_id',)

@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'temperature', 'humidity', 'timestamp')
    list_filter = ('device_id', 'timestamp')
    search_fields = ('device_id',)
