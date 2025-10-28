from django.db import models
from django.utils import timezone
from datetime import datetime, time

class Telemetry(models.Model):
    device_id = models.CharField(max_length=50)
    temperature = models.FloatField()
    humidity = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

class Device(models.Model):
    device_id = models.CharField(max_length=50, unique=True)
    relay_state = models.BooleanField(default=False)
    auto_mode = models.BooleanField(default=True)
    temp_threshold_high = models.FloatField(default=28.0)
    temp_threshold_low = models.FloatField(default=24.0)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.device_id

class DailyLog(models.Model):
    device_id = models.CharField(max_length=50)
    date = models.DateTimeField()  # Changed from DateField to DateTimeField
    avg_temperature = models.FloatField()
    avg_humidity = models.FloatField()
    min_temperature = models.FloatField()
    max_temperature = models.FloatField()
    fan_runtime_minutes = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['device_id', 'date']
