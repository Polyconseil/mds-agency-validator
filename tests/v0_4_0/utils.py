import random

from tests.utils import REGISTERED_DEVICE_ID, get_timestamp


def generate_telemetry():
    return {
        'device_id': REGISTERED_DEVICE_ID,
        'timestamp': get_timestamp(),
        'gps': {
            'lat': random.uniform(-90, 90),
            'lng': random.uniform(-180, 180),
        },
        # TODO if applicable (depends on vehicle propulsion ?) add "charge"
        # confirm if Agency must check with registred vehicle propulsion type
    }
