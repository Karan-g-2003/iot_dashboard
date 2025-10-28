from rest_framework import serializers
from .models import Telemetry, Device, DailyLog

class TelemetrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Telemetry
        fields = ['id', 'device_id', 'temperature', 'humidity', 'timestamp']

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'device_id', 'relay_state', 'auto_mode', 'temp_threshold_high', 
                 'temp_threshold_low', 'last_seen']

class DailyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyLog
        fields = ['device_id', 'date', 'avg_temperature', 'avg_humidity', 
                 'min_temperature', 'max_temperature', 'fan_runtime_minutes']