from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Telemetry, Device, DailyLog
from .serializers import TelemetrySerializer, DeviceSerializer, DailyLogSerializer
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Avg, Min, Max, Count
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate

class TelemetryViewSet(viewsets.ModelViewSet):
    queryset = Telemetry.objects.all()
    serializer_class = TelemetrySerializer

    def list(self, request):
        timespan = request.query_params.get('timespan', '1h')  # Default to 1 hour
        device_id = request.query_params.get('device_id', None)
        
        # Get current time and round to nearest 10 minutes
        now = timezone.now()
        if timespan == '1h':
            # For 1 hour view - data points every 10 minutes
            start_time = now - timedelta(hours=1)
            start_time = start_time.replace(minute=(start_time.minute // 10) * 10, second=0, microsecond=0)
            readings = Telemetry.objects.filter(timestamp__gte=start_time)
            if device_id:
                readings = readings.filter(device_id=device_id)
            
            # Group by 10-minute intervals
            data = []
            current = start_time
            while current <= now:
                next_interval = current + timedelta(minutes=10)
                interval_readings = readings.filter(
                    timestamp__gte=current,
                    timestamp__lt=next_interval
                ).aggregate(
                    avg_temp=Avg('temperature'),
                    avg_hum=Avg('humidity')
                )
                
                data.append({
                    'timestamp': current.isoformat(),
                    'temperature': interval_readings['avg_temp'] if interval_readings['avg_temp'] is not None else 0,
                    'humidity': interval_readings['avg_hum'] if interval_readings['avg_hum'] is not None else 0
                })
                current = next_interval
                
        elif timespan == '24h':
            # For 24 hours view - data points every hour
            start_time = now - timedelta(days=1)
            start_time = start_time.replace(minute=0, second=0, microsecond=0)
            readings = Telemetry.objects.filter(timestamp__gte=start_time)
            if device_id:
                readings = readings.filter(device_id=device_id)
            
            # Group by hour
            data = []
            current = start_time
            while current <= now:
                next_hour = current + timedelta(hours=1)
                hour_readings = readings.filter(
                    timestamp__gte=current,
                    timestamp__lt=next_hour
                ).aggregate(
                    avg_temp=Avg('temperature'),
                    avg_hum=Avg('humidity')
                )
                
                data.append({
                    'timestamp': current.isoformat(),
                    'temperature': hour_readings['avg_temp'] if hour_readings['avg_temp'] is not None else 0,
                    'humidity': hour_readings['avg_hum'] if hour_readings['avg_hum'] is not None else 0
                })
                current = next_hour
                
        elif timespan == '7d':
            # For 7 days view - data points every day
            start_time = now - timedelta(days=7)
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            readings = Telemetry.objects.filter(timestamp__gte=start_time)
            if device_id:
                readings = readings.filter(device_id=device_id)
            
            # Group by day
            data = []
            current = start_time
            while current <= now:
                next_day = current + timedelta(days=1)
                day_readings = readings.filter(
                    timestamp__gte=current,
                    timestamp__lt=next_day
                ).aggregate(
                    avg_temp=Avg('temperature'),
                    avg_hum=Avg('humidity')
                )
                
                data.append({
                    'timestamp': current.isoformat(),
                    'temperature': day_readings['avg_temp'] if day_readings['avg_temp'] is not None else 0,
                    'humidity': day_readings['avg_hum'] if day_readings['avg_hum'] is not None else 0
                })
                current = next_day
        
        return Response(data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            telemetry = serializer.save()
            
            # Get or create device
            device = Device.objects.get_or_create(device_id=telemetry.device_id)[0]
            
            # Auto fan control if auto_mode is enabled
            if device.auto_mode:
                if telemetry.temperature >= device.temp_threshold_high and not device.relay_state:
                    device.relay_state = True
                    device.save()
                elif telemetry.temperature <= device.temp_threshold_low and device.relay_state:
                    device.relay_state = False
                    device.save()
            
            # Update daily log
            today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_log, created = DailyLog.objects.get_or_create(
                device_id=telemetry.device_id,
                date=today,
                defaults={
                    'avg_temperature': telemetry.temperature,
                    'avg_humidity': telemetry.humidity,
                    'min_temperature': telemetry.temperature,
                    'max_temperature': telemetry.temperature,
                }
            )

            if not created:
                # Update the averages and min/max values
                next_day = today + timedelta(days=1)
                today_readings = Telemetry.objects.filter(
                    device_id=telemetry.device_id,
                    timestamp__gte=today,
                    timestamp__lt=next_day
                )
                stats = today_readings.aggregate(
                    avg_temp=Avg('temperature'),
                    avg_hum=Avg('humidity'),
                    min_temp=Min('temperature'),
                    max_temp=Max('temperature')
                )
                
                daily_log.avg_temperature = stats['avg_temp']
                daily_log.avg_humidity = stats['avg_hum']
                daily_log.min_temperature = stats['min_temp']
                daily_log.max_temperature = stats['max_temp']
                
                # Update fan runtime
                if device.relay_state:
                    daily_log.fan_runtime_minutes += 1
                
                daily_log.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    @action(detail=True, methods=['get'])
    def command(self, request, pk=None):
        device = self.get_object()
        return Response({
            'relay': device.relay_state,
            'auto_mode': device.auto_mode,
            'temp_threshold_high': device.temp_threshold_high,
            'temp_threshold_low': device.temp_threshold_low
        })

    @action(detail=True, methods=['post'])
    def set_relay(self, request, pk=None):
        device = self.get_object()
        state = request.data.get('state', None)
        auto = request.data.get('auto_mode', None)
        high_threshold = request.data.get('temp_threshold_high', None)
        low_threshold = request.data.get('temp_threshold_low', None)

        if state is not None and not device.auto_mode:
            device.relay_state = state
            device.save()
        
        if auto is not None:
            device.auto_mode = auto
            device.save()
        
        if high_threshold is not None:
            device.temp_threshold_high = high_threshold
            device.save()
        
        if low_threshold is not None:
            device.temp_threshold_low = low_threshold
            device.save()
            
        return Response({
            'status': 'device updated',
            'relay_state': device.relay_state,
            'auto_mode': device.auto_mode,
            'temp_threshold_high': device.temp_threshold_high,
            'temp_threshold_low': device.temp_threshold_low
        })

class DailyLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyLog.objects.all()
    serializer_class = DailyLogSerializer

    def get_queryset(self):
        queryset = DailyLog.objects.all().order_by('-date')
        days = self.request.query_params.get('days', None)
        device_id = self.request.query_params.get('device_id', None)

        if days is not None:
            start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=int(days))
            queryset = queryset.filter(date__gte=start_date)
        
        if device_id is not None:
            queryset = queryset.filter(device_id=device_id)
        
        return queryset

def dashboard(request):
    return render(request, 'iot_app/dashboard.html')
