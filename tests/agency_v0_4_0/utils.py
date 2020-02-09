from base64 import b64encode
import json
import uuid
import random

from tests import utils


def generate_telemetry():
    return {
        'device_id': str(uuid.uuid4()),
        'timestamp': utils.get_timestamp(),
        'gps': {
            'lat': random.uniform(-90, 90),
            'lng': random.uniform(-180, 180),
        },
        # TODO if applicable (depends on vehicle propulsion ?) add "charge"
    }


def get_request(data):
    # TODO: this is a basic token, not a bearer token
    auth = b64encode(b'username:password').decode('utf8')
    request = {
        'data': json.dumps(data),
        'content_type': 'application/json',
        'headers': {
            'Authorization': 'Bearer %s' % auth
        }
    }
    return request
