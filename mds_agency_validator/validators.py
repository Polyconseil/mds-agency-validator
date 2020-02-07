import os
import yaml
import cerberus
import re


class MdsValidator(cerberus.Validator):
    def _validate_type_uuid(self, value):
        if not isinstance(value, str):
            return False
        re_uuid = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', re.I)
        return bool(re_uuid.match(value))


base_path = os.path.abspath(os.path.dirname(__file__))

path = os.path.join(base_path, 'schemas/agency_v0.4.0/post_vehicle.yaml')
with open(path, 'r') as schema:
    agency_v0_4_0_vehicles = MdsValidator(yaml.safe_load(schema))

path = os.path.join(base_path, 'schemas/agency_v0.4.0/post_vehicle_event.yaml')
with open(path, 'r') as schema:
    agency_v0_4_0_vehicles_event = MdsValidator(yaml.safe_load(schema))
