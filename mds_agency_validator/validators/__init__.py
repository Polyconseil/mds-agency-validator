import cerberus
import json
import os
import re
import yaml

from flask import abort
from flask import request


class MdsValidator(cerberus.Validator):
    def _validate_type_uuid(self, value):
        if not isinstance(value, str):
            return False
        re_uuid = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', re.I)
        return bool(re_uuid.match(value))


base_path = os.path.abspath(os.path.dirname(__file__))

path = os.path.join(base_path, 'schemas/agency_v0.4.0/post_vehicle_event.yaml')
with open(path, 'r') as schema:
    agency_v0_4_0_vehicles_event = MdsValidator(yaml.safe_load(schema))


def check_and_extract_agency_v0_4_0():
    check_authorization()
    # Don't check Content-Type
    # Can't use request.get_json() as Content-Type might be wrong
    return json.loads(request.data.decode('utf8'))


def check_authorization():
    auth = request.headers.get('Authorization')
    if auth is None:
        abort(401, 'No auth provided')
    auth_type, _token = auth.split(' ')
    if auth_type != 'Bearer':
        abort(401, 'Bearer token required')
    # TODO should contain provider_id

    # Maybe use flask-jwt-extended ?
    # https://github.com/vimalloc/flask-jwt-extended/blob/bf1a521b444536a5baea086899636406122acbc5/flask_jwt_extended/view_decorators.py#L267


def is_uuid(value):
    if not isinstance(value, str):
        return False
    re_uuid = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', re.I)
    return bool(re_uuid.match(value))


def agency_v0_4_0_vehicle_register():
    """validate MDS Agency API v0.4.0 Vehicle - Register endpoint"""
    payload = check_and_extract_agency_v0_4_0()
    bad_param = []
    missing_param = []

    try:
        device_id = payload.pop('device_id')
    except KeyError:
        missing_param.append('device_id')
    else:
        if not is_uuid(device_id):
            bad_param.append('device_id')

    # TODO : check already registred

    try:
        vehicle_id = payload.pop('vehicle_id')
    except KeyError:
        missing_param.append('vehicle_id')
    else:
        if not isinstance(vehicle_id, str):
            bad_param.append('vehicle_id')

    # don't use type as it's a python builtin function
    try:
        vehicle_type = payload.pop('type')
    except KeyError:
        missing_param.append('type')
    else:
        allowed_types = ['bicycle', 'car', 'scooter']
        if not vehicle_type in allowed_types:
            bad_param.append('type')

    try:
        propulsion = payload.pop('propulsion')
    except KeyError:
        missing_param.append('propulsion')
    else:
        allowed_propulsions = [
            'human',
            'electric_assist',
            'electric',
            'combustion',
        ]
        if not isinstance(propulsion, list):
            bad_param.append('propulsion')
        if not set(propulsion).issubset(set(allowed_propulsions)):
            bad_param.append('propulsion')

    try:
        year = payload.pop('year')
    except KeyError:
        pass
    else:
        if not isinstance(year, int):
            bad_param.append('year')

    try:
        mfgr = payload.pop('mfgr')
    except KeyError:
        pass
    else:
        if not isinstance(mfgr, str):
            bad_param.append('mfgr')

    try:
        model = payload.pop('model')
    except KeyError:
        pass
    else:
        if not isinstance(model, str):
            bad_param.append('model')

    # Remaining keys
    for param in payload:
        bad_param.append(param)

    result = {}
    if bad_param:
        result['bad_param'] = bad_param
    if missing_param:
        result['missing_param'] = missing_param
    if result:
        abort(400, json.dumps(result))

    return '', 201
