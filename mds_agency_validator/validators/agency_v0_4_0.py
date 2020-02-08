import json

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
        raise NotImplementedError

    def check_payload_is_empty(self):
        """Store remaining keys in bad_params"""
        for param in self.payload:
            self.bad_param.append(param)

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

    def get_field(self, field_name, required=True, from_dict=None):
        """Return the field from the payload, and if it was is_present
        (this 'is_present' boolean allows us to handle None values and absent fields)
        Also add the field name to missing_params if absent and required.
        """
        from_dict = from_dict or self.payload
        try:
            return from_dict.pop(field_name), True
        except KeyError:
            if required:
                self.missing_param.append(field_name)
            return None, False

    def validate(self):
        """Base validation for v0.4.0 Agency API"""
        self.check_authorization()
        # No check on Content-Type
        self.extract_payload()
        self.analyze_payload()
        self.check_payload_is_empty()
        self.raise_on_anomalies()
        return self.valid_response()

    def validate_telemetry(self, telemetry):
        """Validate data against Agency 0.4.0 Telemtry type"""
        if not isinstance(telemetry, dict):
            self.bad_param.append('telemetry')
            return

        device_id, is_present = self.get_field('device_id', from_dict=telemetry)
        if is_present and not utils.is_uuid(device_id):
            self.bad_param.append('device_id')

        timestamp, is_present = self.get_field('timestamp', from_dict=telemetry)
        if is_present and not isinstance(timestamp, int):
            self.bad_param.append('timestamp')

        gps, is_present = self.get_field('gps', from_dict=telemetry)
        if is_present and not isinstance(gps, dict):
            self.bad_param.append('gps')
        elif is_present:

            lat, is_present = self.get_field('lat', from_dict=gps)
            if is_present:
                if not isinstance(lat, float) or lat < -90 or lat > 90:
                    self.bad_param.append('gps.lat')

            lng, is_present = self.get_field('lng', from_dict=gps)
            if is_present:
                if not isinstance(lng, float) or lng < -180 or lng > 180:
                    self.bad_param.append('gps.lng')

            # TODO and so on...

        charge, is_present = self.get_field(
            'charge',
            from_dict=telemetry,
            required=False
        )
        if is_present and not isinstance(charge, float):
            self.bad_param.append('charge')


class AgencyVehicleRegister_v0_4_0(AgencyBaseValidator_v0_4_0):
    """MDS Agency API v0.4.0 Vehicle - Register validator"""

    def analyze_payload(self):
        device_id, is_present = self.get_field('device_id')
        if is_present and not utils.is_uuid(device_id):
            self.bad_param.append('device_id')

        # TODO : check already registred

        vehicle_id, is_present = self.get_field('vehicle_id')
        if is_present and not isinstance(vehicle_id, str):
            self.bad_param.append('vehicle_id')

        # don't use 'type' as var name as it's a python built-in function
        vehicle_type, is_present = self.get_field('type')
        allowed_types = ['bicycle', 'car', 'scooter']
        if is_present and vehicle_type not in allowed_types:
            self.bad_param.append('type')

        propulsion, is_present = self.get_field('propulsion')
        if is_present:
            allowed_propulsions = [
                'human',
                'electric_assist',
                'electric',
                'combustion',
            ]
            if not isinstance(propulsion, list):
                self.bad_param.append('propulsion')
            elif not set(propulsion).issubset(set(allowed_propulsions)):
                self.bad_param.append('propulsion')

        year, is_present = self.get_field('year', required=False)
        if is_present and not isinstance(year, int):
            self.bad_param.append('year')

        mfgr, is_present = self.get_field('mfgr', required=False)
        if is_present and not isinstance(mfgr, str):
            self.bad_param.append('mfgr')

        model, is_present = self.get_field('model', required=False)
        if is_present and not isinstance(model, str):
            self.bad_param.append('model')


class AgencyVehicleEvent_v0_4_0(AgencyBaseValidator_v0_4_0):
    """MDS Agency API v0.4.0 Vehicle - Event validator"""

    def analyze_payload(self):
        event_type, is_present = self.get_field('event_type')
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
        if is_present and event_type not in allowed_event_types:
            self.bad_param.append('event_type')

        # TODO confirm if event_type == deregister implies that
        # event_type_reason is required

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
        # if allowed_event_types_reasons is not empty then the value is excpected
        if allowed_event_types_reasons:
            event_type_reason, is_present = self.get_field('event_type_reason')
            if is_present and event_type_reason not in allowed_event_types_reasons:
                self.bad_param.append('event_type_reason')

        timestamp, is_present = self.get_field('timestamp')
        if is_present and not isinstance(timestamp, int):
            self.bad_param.append('timestamp')

        telemetry, is_present = self.get_field('telemetry')
        # Check telemetry.device_id ?
        if is_present:
            self.validate_telemetry(telemetry)

        if event_type in ['trip_start', 'trip_enter', 'trip_leave', 'trip_end']:
            trip_id, is_present = self.get_field('trip_id')
            if is_present and not utils.is_uuid(trip_id):
                self.bad_param.append('trip_id')
