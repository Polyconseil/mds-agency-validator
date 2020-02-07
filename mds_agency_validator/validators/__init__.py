import json
import os
import re

from flask import abort
from flask import request


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


def agency_v0_4_0_vehicle_event():
    """validate MDS Agency API v0.4.0 Vehicle - Event endpoint"""
    payload = check_and_extract_agency_v0_4_0()
    bad_param = []
    missing_param = []

    try:
        event_type = payload.pop('event_type')
    except KeyError:
        missing_param.append('event_type')
        event_type = None
    else:
        allowed_event_types = [
            'register',
            'service_start',
            'service_end',
            'provider_drop_off',
            'provider_pick_up',
            'city_pick_up',
            'reserve',
            'cancel_reservation',
            'trip_start',
            'trip_enter',
            'trip_leave',
            'trip_end',
            'deregister',
        ]
        if event_type not in allowed_event_types:
            bad_param.append('event_type')

    # TODO confirm if event_type == deregister implies that
    # event_type_reason is required

    allowed_event_types_reasons = []
    if event_type == 'service_end':
        allowed_event_types_reasons = [
            'low_battery',
            'maintenance',
            'compliance',
            'off_hours',
        ]
    elif event_type == 'provider_pick_up':
        allowed_event_types_reasons = [
            'rebalance',
            'maintenance',
            'charge',
            'compliance',
        ]
    elif event_type == 'deregister':
        allowed_event_types_reasons = ['missing', 'decommissioned']
    # if allowed_event_types_reasons is not empty then the value is excpected
    if allowed_event_types_reasons:
        try:
            event_type_reason = payload.pop('event_type_reason')
        except KeyError:
            missing_param.append('event_type_reason')
        else:
            if event_type_reason not in allowed_event_types_reasons:
                bad_param.append('event_type_reason')

    try:
        timestamp = payload.pop('timestamp')
    except KeyError:
        missing_param.append('timestamp')
    else:
        if not isinstance(timestamp, int):
            bad_param.append('timestamp')

    try:
        telemetry = payload.pop('telemetry')
    except KeyError:
        missing_param.append('telemetry')
    else:
        # validate telemetry
        if not isinstance(telemetry, dict):
            bad_param.append('telemetry')

    if event_type in ['trip_start', 'trip_enter', 'trip_leave', 'trip_end']:
        try:
            trip_id = payload.pop('trip_id')
        except KeyError:
            missing_param.append('trip_id')
        else:
            if not is_uuid(trip_id):
                bad_param.append('trip_id')

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
