from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from .models import Device, Telemetry

class MongoAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('devices/', self.admin_view(self.devices_view), name='devices_list'),
            path('telemetry/', self.admin_view(self.telemetry_view), name='telemetry_list'),
        ]
        return custom_urls + urls

    def devices_view(self, request):
        context = {
            'objects': Device.get_all(),
            'title': 'Devices List',
            'opts': {'app_label': 'iot_app', 'model_name': 'device'},
            **self.each_context(request),
        }
        return render(request, 'admin/mongo_changelist.html', context)

    def telemetry_view(self, request):
        context = {
            'objects': Telemetry.get_all(),
            'title': 'Telemetry List',
            'opts': {'app_label': 'iot_app', 'model_name': 'telemetry'},
            **self.each_context(request),
        }
        return render(request, 'admin/mongo_changelist.html', context)

# Create custom admin site instance
mongo_admin = MongoAdminSite(name='mongoadmin')

# Register the admin site
admin.site = mongo_admin
admin.sites.site = mongo_admin