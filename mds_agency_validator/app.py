from flask import Flask

from mds_agency_validator.v0_4_0.routes import v0_4_0_bp
from mds_agency_validator.v1_0_0.routes import blueprint as v1_0_0_bp

app = Flask(__name__, static_folder=None)

# Register routes to all validators using blueprints
app.register_blueprint(v0_4_0_bp, url_prefix='/v0.4.0')
app.register_blueprint(v1_0_0_bp, url_prefix='/v1.0.0')


@app.route('/')
def index():
    urls = sorted(rule.rule for rule in app.url_map.iter_rules())
    return '\n'.join(urls)
