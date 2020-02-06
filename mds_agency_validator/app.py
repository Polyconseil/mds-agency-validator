from jsonschema.exceptions import ValidationError
from jsonschema import validate

from flask import abort
from flask import Flask
from flask import request

from mds_agency_validator import schemas


def create_app():
    app = Flask(__name__, static_folder=None)

    # TODO: use HTTPS and not HTTP
    # Beware of self signed certificats.... curl refuse to post on it

    @app.route('/')
    def index():  # pylint: disable=unused-variable
        urls = sorted(rule.rule for rule in app.url_map.iter_rules())
        return '\n'.join(urls)

    def check_authorization():
        if request.authorization is None:
            abort(401, 'No auth provided')

        # TODO check actual content
        # Should we enforce that there should be a JWT token ?
        # Allow user to set a setting with/without auth checks ?
        # Maybe use flask-jwt-extended ?
        # https://github.com/vimalloc/flask-jwt-extended/blob/bf1a521b444536a5baea086899636406122acbc5/flask_jwt_extended/view_decorators.py#L267

    def check_content_type():
        if request.content_type != 'application/json':
            abort(500, 'Request content type should be application/json')

    @app.route('/v0.4/vehicles', methods=['POST'])
    def agency_v0_4_vehicles():  # pylint: disable=unused-variable
        check_authorization()
        check_content_type()
        try:
            payload = request.get_json()
            validate(instance=payload, schema=schemas.agency_v0_4_0_post_vehicle)
        except ValidationError as e:
            abort(500, 'JsonValidationError : ' + e.message)

        return 'OK'

    return app
