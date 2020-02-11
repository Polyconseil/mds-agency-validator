from flask import Flask

from mds_agency_validator.v0_4_0.routes import v0_4_0_bp


app = Flask(__name__, static_folder=None)
app.register_blueprint(v0_4_0_bp, url_prefix='/v0.4.0')

@app.route('/')
def index():  # pylint: disable=unused-variable
    urls = sorted(rule.rule for rule in app.url_map.iter_rules())
    return '\n'.join(urls)

# TODO: use HTTPS and not HTTP
# Beware of self signed certificats.... curl refuse to post on it
