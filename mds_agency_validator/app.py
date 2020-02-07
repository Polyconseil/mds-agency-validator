import json

from flask import abort
from flask import Flask
from flask import request

from mds_agency_validator import validators


def create_app():
    app = Flask(__name__, static_folder=None)

    # TODO: use HTTPS and not HTTP
    # Beware of self signed certificats.... curl refuse to post on it

    @app.route('/')
    def index():  # pylint: disable=unused-variable
        urls = sorted(rule.rule for rule in app.url_map.iter_rules())
        return '\n'.join(urls)

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

    def check_content_type():  # pylint: disable=unused-variable
        if request.content_type != 'application/json':
            abort(415, 'Request content type should be application/json')

    def check_and_extract_agency_v0_4_0():
        check_authorization()
        # Don't check Content-Type
        # Can't use request.get_json() as Content-Type might be wrong
        return json.loads(request.data.decode('utf8'))

    @app.route('/v0.4.0/vehicles', methods=['POST'])
    def agency_v0_4_0_vehicles():  # pylint: disable=unused-variable
        payload = check_and_extract_agency_v0_4_0()
        validator = validators.agency_v0_4_0_vehicles
        if not validator.validate(payload):
            abort(400, 'JsonValidationError : ' + str(validator.errors))
        # TODO : return correct status and errores as in specs
        # TODO : handle already registred
        return 'OK', 201

    # TODO : add vehicle update

    @app.route('/v0.4.0/vehicles/<device_id>/event', methods=['POST'])
    def agency_v0_4_0_vehicles_event(device_id):  # pylint: disable=unused-variable
        payload = check_and_extract_agency_v0_4_0()
        # TODO check device_id against registered vehicles
        validator = validators.agency_v0_4_0_vehicles_event
        if not validator.validate(payload):
            abort(400, 'JsonValidationError : ' + str(validator.errors))
        # TODO : return correct status and errores as in specs
        return 'OK', 201

    return app
