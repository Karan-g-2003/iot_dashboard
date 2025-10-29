from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['iot_dashboard']

class Device:
    collection = db['devices']

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def get_by_id(cls, device_id):
        return cls.collection.find_one({'device_id': device_id})

    @classmethod
    def get_or_create(cls, device_id):
        device = cls.get_by_id(device_id)
        if not device:
            device = {
                'device_id': device_id,
                'relay_state': False,
                'temp_threshold_high': 30,
                'temp_threshold_low': 20,
                'auto_mode': True,
                'last_seen': datetime.now()
            }
            cls.collection.insert_one(device)
        return device

    @classmethod
    def update(cls, device_id, update_data):
        cls.collection.update_one(
            {'device_id': device_id},
            {'$set': update_data}
        )

class Telemetry:
    collection = db['telemetry']

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def create(cls, device_id, temperature, humidity):
        telemetry = {
            'device_id': device_id,
            'temperature': temperature,
            'humidity': humidity,
            'timestamp': datetime.now()
        }
        return cls.collection.insert_one(telemetry)

    @classmethod
    def get_range(cls, start_time, end_time, device_id=None):
        query = {
            'timestamp': {
                '$gte': start_time,
                '$lt': end_time
            }
        }
        if device_id:
            query['device_id'] = device_id
        return list(cls.collection.find(query))

class DailyLog:
    collection = db['daily_logs']

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def get_or_create(cls, device_id, date):
        log = cls.collection.find_one({
            'device_id': device_id,
            'date': date
        })
        if not log:
            log = {
                'device_id': device_id,
                'date': date,
                'avg_temperature': 0,
                'avg_humidity': 0,
                'min_temperature': None,
                'max_temperature': None,
                'fan_runtime_minutes': 0
            }
            cls.collection.insert_one(log)
        return log

    @classmethod
    def update(cls, device_id, date, update_data):
        cls.collection.update_one(
            {'device_id': device_id, 'date': date},
            {'$set': update_data}
        )