from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'telemetry', views.TelemetryViewSet, basename='telemetry')
router.register(r'devices', views.DeviceViewSet, basename='device')
router.register(r'daily-logs', views.DailyLogViewSet, basename='daily-log')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', views.dashboard, name='dashboard'),
]