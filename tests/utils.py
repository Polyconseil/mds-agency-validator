import datetime
import json
import random
import string
import uuid

import jwt

from mds_agency_validator.cache import cache

REGISTERED_DEVICE_ID = '9bf269ac-4f4c-4ee4-8ea1-6f2c7dfda397'


def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def random_year():
    return random.randint(1800, 2100)


def get_timestamp():
    return int(datetime.datetime.now().timestamp())


def get_request(data):
    token = jwt.encode({'provider_id': str(uuid.uuid4())}, 'secret', algorithm='HS256')
    return {
        'data': json.dumps(data),
        'content_type': 'application/json',
        'headers': {'Authorization': 'Bearer %s' % token},
    }


def register_device():
    device = {
        'device_id': REGISTERED_DEVICE_ID,
        'vehicle_id': 'AM-9863-EZ',
        'type': 'scooter',
        'propulsion': ['electric'],
    }
    cache.set(device['device_id'], device)
    return device
