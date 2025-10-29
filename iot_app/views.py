from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Telemetry, Device, DailyLog
from .serializers import TelemetrySerializer, DeviceSerializer, DailyLogSerializer
from datetime import datetime, timedelta
from django.shortcuts import render
from statistics import mean

class TelemetryViewSet(viewsets.ViewSet):
    def list(self, request):
        timespan = request.query_params.get('timespan', '1h')
        device_id = request.query_params.get('device_id', None)
        
        now = datetime.now()
        if timespan == '1h':
            start_time = now - timedelta(hours=1)
            start_time = start_time.replace(minute=(start_time.minute // 10) * 10, second=0, microsecond=0)
            readings = Telemetry.get_range(start_time, now, device_id)
            
            data = []
            current = start_time
            while current <= now:
                next_interval = current + timedelta(minutes=10)
                interval_readings = [r for r in readings 
                                  if current <= r['timestamp'] < next_interval]
                
                if interval_readings:
                    temperatures = [r['temperature'] for r in interval_readings]
                    humidities = [r['humidity'] for r in interval_readings]
                    avg_temp = mean(temperatures) if temperatures else 0
                    avg_hum = mean(humidities) if humidities else 0
                else:
                    avg_temp = 0
                    avg_hum = 0
                
                data.append({
                    'timestamp': current.isoformat(),
                    'temperature': avg_temp,
                    'humidity': avg_hum
                })
                current = next_interval
                
        elif timespan == '24h':
            start_time = now - timedelta(days=1)
            start_time = start_time.replace(minute=0, second=0, microsecond=0)
            readings = Telemetry.get_range(start_time, now, device_id)
            
            data = []
            current = start_time
            while current <= now:
                next_hour = current + timedelta(hours=1)
                hour_readings = [r for r in readings 
                               if current <= r['timestamp'] < next_hour]
                
                if hour_readings:
                    temperatures = [r['temperature'] for r in hour_readings]
                    humidities = [r['humidity'] for r in hour_readings]
                    avg_temp = mean(temperatures) if temperatures else 0
                    avg_hum = mean(humidities) if humidities else 0
                else:
                    avg_temp = 0
                    avg_hum = 0
                
                data.append({
                    'timestamp': current.isoformat(),
                    'temperature': avg_temp,
                    'humidity': avg_hum
                })
                current = next_hour
                
        elif timespan == '7d':
            start_time = now - timedelta(days=7)
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            readings = Telemetry.get_range(start_time, now, device_id)
            
            data = []
            current = start_time
            while current <= now:
                next_day = current + timedelta(days=1)
                day_readings = [r for r in readings 
                              if current <= r['timestamp'] < next_day]
                
                if day_readings:
                    temperatures = [r['temperature'] for r in day_readings]
                    humidities = [r['humidity'] for r in day_readings]
                    avg_temp = mean(temperatures) if temperatures else 0
                    avg_hum = mean(humidities) if humidities else 0
                else:
                    avg_temp = 0
                    avg_hum = 0
                
                data.append({
                    'timestamp': current.isoformat(),
                    'temperature': avg_temp,
                    'humidity': avg_hum
                })
                current = next_day
        
        return Response(data)

    def create(self, request):
        serializer = TelemetrySerializer(data=request.data)
        if serializer.is_valid():
            # Create telemetry record
            telemetry = Telemetry.create(
                device_id=serializer.validated_data['device_id'],
                temperature=serializer.validated_data['temperature'],
                humidity=serializer.validated_data['humidity']
            )
            
            # Get or create device
            device = Device.get_or_create(serializer.validated_data['device_id'])
            
            # Auto fan control if auto_mode is enabled
            if device['auto_mode']:
                if serializer.validated_data['temperature'] >= device['temp_threshold_high'] and not device['relay_state']:
                    Device.update(device['device_id'], {'relay_state': True})
                elif serializer.validated_data['temperature'] <= device['temp_threshold_low'] and device['relay_state']:
                    Device.update(device['device_id'], {'relay_state': False})
            
            # Update daily log
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_log = DailyLog.get_or_create(device['device_id'], today)
            
            # Get today's readings
            today_readings = Telemetry.get_range(today, today + timedelta(days=1), device['device_id'])
            
            if today_readings:
                temperatures = [r['temperature'] for r in today_readings]
                humidities = [r['humidity'] for r in today_readings]
                
                DailyLog.update(device['device_id'], today, {
                    'avg_temperature': mean(temperatures),
                    'avg_humidity': mean(humidities),
                    'min_temperature': min(temperatures),
                    'max_temperature': max(temperatures),
                    'fan_runtime_minutes': daily_log['fan_runtime_minutes'] + (1 if device['relay_state'] else 0)
                })

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeviceViewSet(viewsets.ViewSet):
    def list(self, request):
        devices = Device.get_all()
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        device = Device.get_by_id(pk)
        if device is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = DeviceSerializer(device)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def command(self, request, pk=None):
        device = Device.get_by_id(pk)
        if device is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({
            'relay': device['relay_state'],
            'auto_mode': device['auto_mode'],
            'temp_threshold_high': device['temp_threshold_high'],
            'temp_threshold_low': device['temp_threshold_low']
        })

    @action(detail=True, methods=['post'])
    def set_relay(self, request, pk=None):
        device = Device.get_by_id(pk)
        if device is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        update_data = {}
        if 'state' in request.data and not device['auto_mode']:
            update_data['relay_state'] = request.data['state']
        
        if 'auto_mode' in request.data:
            update_data['auto_mode'] = request.data['auto_mode']
        
        if 'temp_threshold_high' in request.data:
            update_data['temp_threshold_high'] = request.data['temp_threshold_high']
        
        if 'temp_threshold_low' in request.data:
            update_data['temp_threshold_low'] = request.data['temp_threshold_low']
        
        if update_data:
            Device.update(pk, update_data)
            device = Device.get_by_id(pk)
            
        return Response({
            'status': 'device updated',
            'relay_state': device['relay_state'],
            'auto_mode': device['auto_mode'],
            'temp_threshold_high': device['temp_threshold_high'],
            'temp_threshold_low': device['temp_threshold_low']
        })

class DailyLogViewSet(viewsets.ViewSet):
    def list(self, request):
        days = request.query_params.get('days', None)
        device_id = request.query_params.get('device_id', None)
        
        now = datetime.now()
        if days:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=int(days))
        else:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
        logs = DailyLog.collection.find({
            'date': {'$gte': start_date},
            **(({'device_id': device_id} if device_id else {}))
        }).sort('date', -1)
        
        serializer = DailyLogSerializer(list(logs), many=True)
        return Response(serializer.data)

def dashboard(request):
    return render(request, 'iot_app/dashboard.html')