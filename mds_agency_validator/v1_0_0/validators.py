import json

from flask import abort

from mds_agency_validator.cache import cache
from mds_agency_validator.validators import BaseValidator

ALLOWED_STATE_TRANSITIONS = {
    'available': [
        'agency_drop_off',
        'battery_charged',
        'maintenance',
        'on_hours',
        'provider_drop_off',
        'reservation_cancel',
        'system_resume',
        'trip_cancel',
        'trip_end',
    ],
    'elsewhere': ['trip_leave_jurisdiction'],
    'non_operational': [
        'battery_low',
        'maintenance',
        'off_hours',
        'system_suspend',
        'unspecified',
    ],
    'on_trip': ['trip_start', 'trip_enter_jurisdiction'],
    'removed': [
        'agency_pick_up',
        'compliance_pick_up',
        'decommissioned',
        'maintenance_pick_up',
        'rebalance_pick_up',
        'system_suspend',
    ],
    'reserved': ['reservation_start'],
    'unknown': ['comms_lost', 'missing'],
}


class Agency1_0_0Validator(BaseValidator):
    schema_prefix = 'v1_0_0/schemas'


class VehicleRegister(Agency1_0_0Validator):

    schema_name = 'vehicle_register.yaml'

    def additional_checks(self):
        device_id = self.payload.get('device_id', None)
        if device_id and cache.get(device_id):
            abort(409, 'already_registered')


class VehicleUpdate(Agency1_0_0Validator):

    schema_name = 'vehicle_update.yaml'

    def __init__(self, device_id, **kwargs):
        super().__init__(**kwargs)
        self.device_id = device_id

    def additional_checks(self):
        if not cache.get(self.device_id):
            abort(404)


class VehicleEvent(Agency1_0_0Validator):

    schema_name = 'vehicle_event.yaml'

    def __init__(self, device_id, **kwargs):
        super().__init__(**kwargs)
        self.device_id = device_id

    def additional_checks(self):
        if not cache.get(self.device_id):
            abort(404)

        # compare route device_id and telemetry device_id
        # We already checked that telemetry is present and contains a device_id with cerberus
        telemetry = self.payload.get('telemetry', {})
        if isinstance(telemetry, dict):
            device_id = telemetry.get('device_id', None)
            if device_id and device_id != self.device_id:
                self.bad_param.append('device_id')

        # event_type value affects event_type_reason and trip_id
        try:
            vehicle_state = self.payload['vehicle_state']
        except KeyError:
            self.missing_param.append('vehicle_state')
            abort(400)

        try:
            event_types = set(self.payload['event_types'])
        except KeyError:
            self.missing_param.append('event_types')
            abort(400)

        if not event_types & {'comms_restored', 'located'}:
            allowed_event_types = ALLOWED_STATE_TRANSITIONS[vehicle_state]
            if not event_types & set(allowed_event_types) and not 'unspecified' in event_types:
                self.bad_param.append('event_types')

        # Check trip_id
        if event_types & {
            'trip_start',
            'trip_cancel',
            'trip_enter_jurisdiction',
            'trip_leave_jurisdiction',
            'trip_end',
        }:
            if 'trip_id' not in self.payload:
                self.missing_param.append('trip_id')
        else:
            if 'trip_id' in self.payload:
                self.bad_param.append('trip_id')


class VehicleTelemetry(Agency1_0_0Validator):

    schema_name = 'vehicle_telemetry.yaml'

    def __init__(self):
        super().__init__()
        self.result = 0
        self.failures = []

    def analyze_payload(self):
        # Replace base cerberus errors parsing
        self.cerberus_validator.validate(self.payload)
        # on this payload (list of dict) the errors will be a list with only one dict inside
        # containing the list index as keys :
        # errors = [{0: {<anomalies on first telemetry>},  {<anomalies on 2nd telemetry>}}]
        # We need to store failures in self.failures to return them in 201 Success responses
        errors = self.cerberus_validator.errors.get('data', [{}])[0]
        data = self.payload['data']
        for i, telemetry in enumerate(data):
            # if cerberus found an error, or if device isn't registred
            if i in errors or not cache.get(telemetry.get('device_id', None)):
                self.failures.append(data[i])

        self.result = len(data) - len(self.failures)

    def raise_on_anomalies(self):
        # TODO : check response data format
        # Are bad_params and missing_params also required ?
        if self.result == 0:
            abort(400, 'invalid_data')

    def valid_response(self):
        data = json.dumps({'result': self.result, 'failures': self.failures})
        return data, 201
