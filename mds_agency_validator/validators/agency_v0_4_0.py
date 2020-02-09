import json
import os
import yaml

from flask import abort
from flask import request

from . import utils


class AgencyBaseValidator_v0_4_0:
    """Base class for all Agency v0.4.0 validators"""

    class Meta:
        abstract = True

    def __init__(self):
        self.bad_param = []
        self.missing_param = []
        self.payload = None
        self.base_path = os.path.abspath(os.path.dirname(__file__))
        self.load_cerberus_validator()

    def load_cerberus_validator(self):
        path = os.path.join(self.base_path, self.schema_name)
        with open(path, 'r') as schema:
            self.cerberus_validator = utils.MdsValidator(yaml.safe_load(schema))

    def check_authorization(self):
        """Check request authorization"""
        auth = request.headers.get('Authorization')
        if auth is None:
            abort(401, 'No auth provided')
        auth_type, _token = auth.split(' ')
        if auth_type != 'Bearer':
            abort(401, 'Bearer token required')
        # TODO should contain provider_id

        # Maybe use flask-jwt-extended ?
        # https://github.com/vimalloc/flask-jwt-extended/blob/bf1a521b444536a5baea086899636406122acbc5/flask_jwt_extended/view_decorators.py#L267

    def extract_payload(self):
        """Extract payload from request"""
        # Can't use request.get_json() as Content-Type might be wrong
        self.payload = json.loads(request.data.decode('utf8'))

    def analyze_payload(self):
        """Use cerberus for base checks"""
        self.cerberus_validator.validate(self.payload)
        for field, error in self.cerberus_validator.errors.items():
            if error == ['required field']:
                self.missing_param.append(field)
            else:
                self.bad_param.append(field)

    def additional_checks(self):
        """Override this method to add tests"""

    def raise_on_anomalies(self):
        """Check that bad_params and missing_params are empty"""
        result = {}
        if self.bad_param:
            result['bad_param'] = self.bad_param
        if self.missing_param:
            result['missing_param'] = self.missing_param
        if result:
            abort(400, json.dumps(result))

    def valid_response(self):
        """Return that everything went well"""
        return '', 201

    def validate(self):
        """Base validation for v0.4.0 Agency API"""
        self.check_authorization()
        # No check on Content-Type
        self.extract_payload()
        self.analyze_payload()
        self.additional_checks()
        self.raise_on_anomalies()
        return self.valid_response()


class AgencyVehicleRegister_v0_4_0(AgencyBaseValidator_v0_4_0):
    """MDS Agency API v0.4.0 Vehicle - Register validator"""

    schema_name = 'schemas/agency_v0.4.0/vehicle_register.yaml'

    def additional_checks(self):
        # TODO : check vehicle is not already registred
        pass


class AgencyVehicleEvent_v0_4_0(AgencyBaseValidator_v0_4_0):
    """MDS Agency API v0.4.0 Vehicle - Event validator"""

    schema_name = 'schemas/agency_v0.4.0/vehicle_event.yaml'

    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id

    def additional_checks(self):
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