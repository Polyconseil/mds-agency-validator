from flask import Flask

from mds_agency_validator import validators


def create_app():
    app = Flask(__name__, static_folder=None)

    # TODO: use HTTPS and not HTTP
    # Beware of self signed certificats.... curl refuse to post on it

    @app.route('/')
    def index():  # pylint: disable=unused-variable
        urls = sorted(rule.rule for rule in app.url_map.iter_rules())
        return '\n'.join(urls)


    @app.route('/v0.4.0/vehicles', methods=['POST'])
    def agency_v0_4_0_vehicle_register():  # pylint: disable=unused-variable
        return validators.AgencyVehicleRegister_v0_4_0().validate()

    @app.route('/v0.4.0/vehicles/<device_id>', methods=['POST'])
    def agency_v0_4_0_vehicle_update(device_id):  # pylint: disable=unused-variable
        # TODO check device_id against registered vehicles
        return validators.AgencyVehicleUpdate_v0_4_0().validate()

    @app.route('/v0.4.0/vehicles/<device_id>/event', methods=['POST'])
    def agency_v0_4_0_vehicles_event(device_id):  # pylint: disable=unused-variable
        # TODO check device_id against registered vehicles
        return validators.AgencyVehicleEvent_v0_4_0(device_id).validate()

    return app
