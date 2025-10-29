from rest_framework import serializers
from .models import Device, Telemetry, DailyLog

class TelemetrySerializer(serializers.Serializer):
    device_id = serializers.CharField()
    temperature = serializers.FloatField()
    humidity = serializers.FloatField()
    timestamp = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        return Telemetry.create(
            device_id=validated_data['device_id'],
            temperature=validated_data['temperature'],
            humidity=validated_data['humidity']
        )

class DeviceSerializer(serializers.Serializer):
    device_id = serializers.CharField()
    relay_state = serializers.BooleanField(default=False)
    temp_threshold_high = serializers.FloatField(default=30)
    temp_threshold_low = serializers.FloatField(default=20)
    auto_mode = serializers.BooleanField(default=True)
    last_seen = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        return Device.get_or_create(validated_data['device_id'])

    def update(self, instance, validated_data):
        Device.update(instance['device_id'], validated_data)
        return Device.get_by_id(instance['device_id'])

class DailyLogSerializer(serializers.Serializer):
    device_id = serializers.CharField()
    date = serializers.DateTimeField()
    avg_temperature = serializers.FloatField()
    avg_humidity = serializers.FloatField()
    min_temperature = serializers.FloatField(allow_null=True)
    max_temperature = serializers.FloatField(allow_null=True)
    fan_runtime_minutes = serializers.IntegerField()