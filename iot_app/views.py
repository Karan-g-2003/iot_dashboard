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
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=int(days))
            queryset = queryset.filter(date__gte=start_date)
        
        if device_id is not None:
            queryset = queryset.filter(device_id=device_id)
        
        return queryset

def dashboard(request):
    return render(request, 'iot_app/dashboard.html')
