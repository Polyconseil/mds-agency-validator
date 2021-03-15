import json
import os
import re
from collections import defaultdict

import cerberus
import jwt
import yaml
from flask import abort, request


class MdsValidator(cerberus.Validator):
    """Our custom cerberus validator

    We added an uuid type that is a string formated uuid
    """

    def _validate_type_uuid(self, value):
        if not isinstance(value, str):
            return False
        re_uuid = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', re.I)
        return bool(re_uuid.match(value))


class BaseValidator:
    """Base class for all Agency validators

    To use children classes, call validate() on class instance.
    This will perform the following steps :

    - Check the request authorization.
      MDS Agency requires a JWT Bearer token with a provider_id.
    - Extract json payload
    - Base payload analysis using cerberus to check field values and requirements
    - Additional checks from child class, such as conditional allowed values.
      These are painful to write with cerberus, and painful to read.
      We need this validator to be easy to proofread, so this additional tests
      are performed in python
    - Raise error (through flask.abort) on anomalies
    - Return the valid response if no anomaly was found
    """

    schema_prefix = None
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
        path = os.path.join(base_path, self.schema_prefix)
        path = os.path.join(path, self.schema_name)
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
            data = jwt.decode(token, options={'verify_signature': False}, algorithms='HS256')
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
