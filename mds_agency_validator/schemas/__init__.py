import os
import json


base_path = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(base_path, 'agency_v0.3.2/post_vehicle.json'), 'r') as json_schema:
    agency_v0_3_2_post_vehicle = json.load(json_schema)

with open(os.path.join(base_path, 'agency_v0.3.2/post_vehicle_event.json'), 'r') as json_schema:
    agency_v0_3_2_post_vehicle_event = json.load(json_schema)

with open(os.path.join(base_path, 'agency_v0.3.2/post_vehicle_telemetry.json'), 'r') as json_schema:
    agency_v0_3_2_post_vehicle_telemetry = json.load(json_schema)

with open(os.path.join(base_path, 'agency_v0.4.0/post_vehicle.json'), 'r') as json_schema:
    agency_v0_4_0_post_vehicle = json.load(json_schema)

with open(os.path.join(base_path, 'agency_v0.4.0/post_vehicle_event.json'), 'r') as json_schema:
    agency_v0_4_0_post_vehicle_event = json.load(json_schema)

with open(os.path.join(base_path, 'agency_v0.4.0/post_vehicle_telemetry.json'), 'r') as json_schema:
    agency_v0_4_0_post_vehicle_telemetry = json.load(json_schema)
