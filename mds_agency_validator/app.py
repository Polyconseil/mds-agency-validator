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

    def check_content_type():  # pylint: disable=unused-variable
        if request.content_type != 'application/json':
            abort(415, 'Request content type should be application/json')

    @app.route('/v0.4.0/vehicles', methods=['POST'])
    def agency_v0_4_0_vehicle_register():  # pylint: disable=unused-variable
        return validators.agency_v0_4_0_vehicle_register()

    # TODO : add vehicle update

    @app.route('/v0.4.0/vehicles/<device_id>/event', methods=['POST'])
    def agency_v0_4_0_vehicles_event(device_id):  # pylint: disable=unused-variable
        payload = validators.check_and_extract_agency_v0_4_0()
        # TODO check device_id against registered vehicles
        validator = validators.agency_v0_4_0_vehicles_event
        if not validator.validate(payload):
            abort(400, 'JsonValidationError : ' + str(validator.errors))
        # TODO : return correct status and errores as in specs
        return 'OK', 201

    return app
