from flask import Blueprint

from mds_agency_validator.cache import cache

from . import validators

blueprint = Blueprint('v1_0_0', __name__)


@blueprint.route('/vehicles', methods=['POST'])
def vehicle_register():
    validator = validators.VehicleRegister()
    result = validator.validate()
    cache.set(validator.payload['device_id'], validator.payload)
    return result


@blueprint.route('/vehicles/<device_id>', methods=['POST'])
def vehicle_update(device_id):
    return validators.VehicleUpdate(device_id).validate()


@blueprint.route('/vehicles/<device_id>/event', methods=['POST'])
def vehicle_event(device_id):
    return validators.VehicleEvent(device_id).validate()


@blueprint.route('/vehicles/telemetry', methods=['POST'])
def vehicle_telemetry():
    return validators.VehicleTelemetry().validate()
