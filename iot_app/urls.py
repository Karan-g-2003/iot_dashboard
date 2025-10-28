from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'telemetry', views.TelemetryViewSet)
router.register(r'devices', views.DeviceViewSet)  # Changed from 'device' to 'devices'
router.register(r'daily-logs', views.DailyLogViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('', views.dashboard, name='dashboard'),
]