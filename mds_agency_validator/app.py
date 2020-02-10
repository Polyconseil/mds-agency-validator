from flask import Flask


from mds_agency_validator import validators
from mds_agency_validator import cache


def create_app():
    app = Flask(__name__, static_folder=None)

    # TODO: use HTTPS and not HTTP
    # Beware of self signed certificats.... curl refuse to post on it

    @app.route('/')
    def index():  # pylint: disable=unused-variable
        urls = sorted(rule.rule for rule in app.url_map.iter_rules())
        return '\n'.join(urls)

    # TODO Add get_vehicle when storing registred vehicles

    @app.route('/v0.4.0/vehicles', methods=['POST'])
    def agency_v0_4_0_vehicle_register():  # pylint: disable=unused-variable
        validator = validators.AgencyVehicleRegister_v0_4_0()
        result = validator.validate()
        cache.set(validator.payload['device_id'], validator.payload)
        return result

    @app.route('/v0.4.0/vehicles/<device_id>', methods=['POST'])
    def agency_v0_4_0_vehicle_update(device_id):  # pylint: disable=unused-variable
        return validators.AgencyVehicleUpdate_v0_4_0(device_id).validate()

    @app.route('/v0.4.0/vehicles/<device_id>/event', methods=['POST'])
    def agency_v0_4_0_vehicles_event(device_id):  # pylint: disable=unused-variable
        return validators.AgencyVehicleEvent_v0_4_0(device_id).validate()

    @app.route('/v0.4.0/vehicles/telemetry', methods=['POST'])
    def agency_v0_4_0_vehicles_telemetry():  # pylint: disable=unused-variable
        return validators.AgencyVehicleTelemetry_v0_4_0().validate()

    return app
