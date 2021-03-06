from typing import Type

from redis import Redis
import json

from src.configs.settings import REDIS_HOST, REDIS_PORT
from src.shared.constants import INTEL_REQUEST, IntelRequestType
from src.shared.type import IntelResult


class Queue:
    def __init__(self):
        self._UTF_8 = 'utf-8'
        self._redis = Redis(host=REDIS_HOST, port=REDIS_PORT)

    def _rpush(self, name, data):
        return self._redis.rpush(name, data)

    def _lpop(self, name):
        value = self._redis.lpop(name)
        return value.decode(self._UTF_8) if value else value


class BotQueue(Queue):
    def send_request_intel(self, event_id: str, response_event_to: str, location: str, extra: dict):
        request = {
            'event_id': event_id,
            'request_type': IntelRequestType.LOCATION.value,
            'response_event_to': response_event_to,
            'location_name': location,
            'extra': extra
        }
        return self._rpush(INTEL_REQUEST, json.dumps(request))

    def send_request_intel_by_position(self, event_id: str, response_event_to: str, latitude: float, longitude: float, extra: dict):
        request = {
            'event_id': event_id,
            'request_type': IntelRequestType.POSITION.value,
            'response_event_to': response_event_to,
            'position': {
                'lat': latitude,
                'lon': longitude,
            },
            'extra': extra
        }
        return self._rpush(INTEL_REQUEST, json.dumps(request))

    def receive_response_intel(self, response_event_to):
        data = self._lpop(response_event_to)
        return json.loads(data) if data else data


class WorkerQueue(Queue):
    def receive_request_intel(self):
        data = self._lpop(INTEL_REQUEST)
        return json.loads(data) if data else data

    def send_response_intel(self, event_id: str, response_event_to: str, result: Type[IntelResult], extra):
        data = {
            'event_id': event_id,
            'result': {
                'success': result.success,
                'file_url': result.file_url,
                'file_path': result.file_path,
                'address': result.address,
                'error_message': result.error_message,
                'timestamp': str(result.timestamp),
                'intel_url': result.intel_url,
                'location': {
                    'lat': result.location.latitude,
                    'lon': result.location.longitude,
                }
            },
            'extra': extra,
        }
        return self._rpush(response_event_to, json.dumps(data))
