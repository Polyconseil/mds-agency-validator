from flask import Flask

from mds_agency_validator.v0_4_0.routes import v0_4_0_bp

app = Flask(__name__, static_folder=None)

# Register routes to all validators using blueprints
app.register_blueprint(v0_4_0_bp, url_prefix='/v0.4.0')
# Add new supported API version here ^


@app.route('/')
def index():
    """Return all available urls"""
    urls = sorted(rule.rule for rule in app.url_map.iter_rules())
    return '\n'.join(urls)
