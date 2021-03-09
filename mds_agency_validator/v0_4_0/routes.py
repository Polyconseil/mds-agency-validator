from flask import Blueprint

from mds_agency_validator.cache import cache

from . import validators

# Create Blueprint for all v0.4.0 routes below
v0_4_0_bp = Blueprint('v0_4_0', __name__)

# TODO Add get_vehicle ?


@v0_4_0_bp.route('/vehicles', methods=['POST'])
def vehicle_register():  # pylint: disable=unused-variable
    validator = validators.VehicleRegister_v0_4_0()
    result = validator.validate()
    cache.set(validator.payload['device_id'], validator.payload)
    return result


@v0_4_0_bp.route('/vehicles/<device_id>', methods=['POST'])
def vehicle_update(device_id):  # pylint: disable=unused-variable
    return validators.VehicleUpdate_v0_4_0(device_id).validate()


@v0_4_0_bp.route('/vehicles/<device_id>/event', methods=['POST'])
def vehicle_event(device_id):  # pylint: disable=unused-variable
    return validators.VehicleEvent_v0_4_0(device_id).validate()


@v0_4_0_bp.route('/vehicles/telemetry', methods=['POST'])
def vehicle_telemetry():  # pylint: disable=unused-variable
    return validators.VehicleTelemetry_v0_4_0().validate()
