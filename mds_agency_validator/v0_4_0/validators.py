import json

from flask import abort

from mds_agency_validator.cache import cache
from mds_agency_validator.validators import BaseValidator


class Agency0_4_0Validator(BaseValidator):
    schema_prefix = 'v0_4_0/schemas'


class VehicleRegister_v0_4_0(Agency0_4_0Validator):

    schema_name = 'vehicle_register.yaml'

    def additional_checks(self):
        device_id = self.payload.get('device_id', None)
        if device_id and cache.get(device_id):
            abort(409, 'already_registered')


class VehicleUpdate_v0_4_0(Agency0_4_0Validator):

    schema_name = 'vehicle_update.yaml'

    def __init__(self, device_id, **kwargs):
        super().__init__(**kwargs)
        self.device_id = device_id

    def additional_checks(self):
        if not cache.get(self.device_id):
            abort(404)


class VehicleEvent_v0_4_0(Agency0_4_0Validator):

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
        event_type = self.payload.get('event_type', None)
        if event_type:
            # Check event_type_reason values
            event_type_to_event_types_reasons = {
                'service_end': [
                    'low_battery',
                    'maintenance',
                    'compliance',
                    'off_hours',
                ],
                'provider_pick_up': [
                    'rebalance',
                    'maintenance',
                    'charge',
                    'compliance',
                ],
                'deregister': [
                    'missing',
                    'decommissioned',
                ],
            }
            allowed_event_types_reasons = event_type_to_event_types_reasons.get(event_type, None)
            if allowed_event_types_reasons:
                # event_type_reason is required
                try:
                    event_type_reason = self.payload['event_type_reason']
                except KeyError:
                    self.missing_param.append('event_type_reason')
                    # TODO confirm if event_type == deregister implies that
                    # event_type_reason is required
                else:
                    if event_type_reason not in allowed_event_types_reasons:
                        self.bad_param.append('event_type_reason')
            elif 'event_type_reason' in self.payload:
                # event_type_reason should not be there
                self.bad_param.append('event_type_reason')

            # Check trip_id
            if event_type in ['trip_start', 'trip_enter', 'trip_leave', 'trip_end']:
                if 'trip_id' not in self.payload:
                    self.missing_param.append('trip_id')
            else:
                if 'trip_id' in self.payload:
                    self.bad_param.append('trip_id')


class VehicleTelemetry_v0_4_0(Agency0_4_0Validator):

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
