import json
import random
import uuid

import jwt

from tests import utils

from .conftest import REGISTRED_DEVICE_ID


def generate_telemetry():
    return {
        'device_id': REGISTRED_DEVICE_ID,
        'timestamp': utils.get_timestamp(),
        'gps': {
            'lat': random.uniform(-90, 90),
            'lng': random.uniform(-180, 180),
        },
        # TODO if applicable (depends on vehicle propulsion ?) add "charge"
        # confirm if Agency must check with registred vehicle propulsin type
    }


def get_request(data):
    token = jwt.encode({'provider_id': str(uuid.uuid4())}, 'secret').decode('utf8')
    request = {
        'data': json.dumps(data),
        'content_type': 'application/json',
        'headers': {'Authorization': 'Bearer %s' % token},
    }
    return request
