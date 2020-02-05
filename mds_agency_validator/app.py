from flask import Flask
from flask import request
from flask import url_for


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():  #pylint: disable=unused-variable
        urls = [
            url_for('index'),
            url_for('agency_v0_4'),
        ]
        return '\n'.join(urls)

    @app.route('/v0.4', methods=['POST'])
    def agency_v0_4():  #pylint: disable=unused-variable
        ###########################################################################
        # Check headers

        # Content type should be application/json
        # FIXME: use correct HTTP response
        assert request.content_type == 'application/json'

        ###########################################################################
        # Check json payload

        # This only works if content type is set to application/json
        _payload = request.get_json()

        # FIXME: check payload against json schema file
        # retrieve the file from https://github.com/openmobilityfoundation/mobility-data-specification/tree/dev/agency

        return 'OK'

    return app
