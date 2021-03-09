import json
import os
from collections import defaultdict

import jwt
import yaml
from flask import abort, request

from mds_agency_validator.cache import cache
from mds_agency_validator.validation_tools import MdsValidator


class BaseValidator_v0_4_0:
    """Base class for all Agency v0.4.0 validators

    To use children classes, call validate() on class instance.
    This will perform the following steps :

    - Check the request authorization.
      MDS Agency 0.4.0 requires a JWT Bearer token with a provider_id.
    - Extract json payload
    - Base payload analysis using cerberus to check field values and requirements
    - Additional checks from child class, such as conditional allowed values.
      These are painful to write with cerberus, and painful to read.
      We need this validator to be easy to proofread, so this additional tests
      are performed in python
    - Raise error (through falsk.abort) on anomalies
    - Return the valid response if no anomaly was found
    """

    schema_name = None

    class Meta:
        abstract = True

    def __init__(self):
        self.bad_param = []
        self.missing_param = []
        self.payload = None
        self.load_cerberus_validator()

    def load_cerberus_validator(self):
        """Load yaml file from class schema_name,
        then create an instance of our custom cerberus validator
        """
        base_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(base_path, self.schema_name)
        with open(path, 'r') as schema:
            self.cerberus_validator = MdsValidator(yaml.safe_load(schema))

    def check_authorization(self):
        """Check request authorization"""
        auth = request.headers.get('Authorization')
        if auth is None:
            abort(401, 'Please provide an Authorization')
        # We need a bearer token
        auth_type, token = auth.split(' ')
        if auth_type != 'Bearer':
            abort(401, 'Please provide a Bearer token')
        # provider_id should be present
        try:
            data = jwt.decode(token, verify=False)
        except jwt.exceptions.DecodeError:
            abort(401, 'Please provide a valid JWT')
        else:
            if 'provider_id' not in data:
                abort(401, 'Please provide a provider_id')

    def extract_payload(self):
        """Extract payload from request"""
        # We cannot use request.get_json() because it only works if Content-Type is
        # application/json and Agency API v0.4.0 specs don't enforce the Content-Type
        self.payload = json.loads(request.data.decode('utf8'))

    def analyze_payload(self):
        """Use our custom cerberus validator for base checks"""
        self.cerberus_validator.validate(self.payload)
        # Flatten errors on nested fields
        flat_errors = self.flatten_errors(self.cerberus_validator.errors)
        # Sort errors between missing fields and bad fields value
        for field, errors in flat_errors.items():
            if 'required field' in errors:
                self.missing_param.append(field)
            else:
                self.bad_param.append(field)

    def flatten_errors(self, errors):
        """Flatten cerberus errors on nested schema"""
        # TODO : add test suite on this function
        flat_errors = defaultdict(list)
        for field, field_errors in errors.items():
            for field_error in field_errors:
                # if field_error is a string, then it's not nested
                if isinstance(field_error, str):
                    flat_errors[field].append(field_error)
                else:
                    # field is nested, and is a dict
                    # each dict key is a field name (or index if it's in a list).
                    field_flat_errors = self.flatten_errors(field_error)
                    for key, value in field_flat_errors.items():
                        flat_errors[field + '.' + key].extend(value)
        return flat_errors

    def additional_checks(self):
        """Additional checks performed after basic cerberus validation.
        Override this method in child class to add advance checks
        """

    def raise_on_anomalies(self):
        """Raise Http error if any anomaly was found.
        By default, it's when bad_params or missing_params are not empty
        but you can add new anomalies in child class
        """
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


class VehicleRegister_v0_4_0(BaseValidator_v0_4_0):
    """MDS Agency API v0.4.0 Vehicle - Register validator"""

    schema_name = 'schemas/vehicle_register.yaml'

    def additional_checks(self):
        device_id = self.payload.get('device_id', None)
        if device_id and cache.get(device_id):
            abort(409, 'already_registered')


class VehicleUpdate_v0_4_0(BaseValidator_v0_4_0):
    """MDS Agency API v0.4.0 Vehicle - Update validator"""

    schema_name = 'schemas/vehicle_update.yaml'

    def __init__(self, device_id, **kwargs):
        super().__init__(**kwargs)
        self.device_id = device_id

    def additional_checks(self):
        if not cache.get(self.device_id):
            abort(404)


class VehicleEvent_v0_4_0(BaseValidator_v0_4_0):
    """MDS Agency API v0.4.0 Vehicle - Event validator"""

    schema_name = 'schemas/vehicle_event.yaml'

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


class VehicleTelemetry_v0_4_0(BaseValidator_v0_4_0):
    """MDS Agency API v0.4.0 Vehicle - Update validator"""

    schema_name = 'schemas/vehicle_telemetry.yaml'

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
