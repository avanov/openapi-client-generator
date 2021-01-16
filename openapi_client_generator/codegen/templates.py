from jinja2 import Environment, PackageLoader, Template, StrictUndefined


templates = Environment(
    loader=PackageLoader('openapi_client_generator', 'codegen/templates'),
    undefined=StrictUndefined  # raise exception on missing variables
)


README: Template        = templates.get_template('README.md.j2')
MANIFEST: Template      = templates.get_template('MANIFEST.in.j2')
SETUP_PY: Template      = templates.get_template('setup.py.j2')
REQUIREMENTS: Template  = templates.get_template('requirements.txt.j2')
ENDPOINT: Template      = templates.get_template('endpoint.py.j2')
ENDPOINT_INIT: Template = templates.get_template('endpoint_init.py.j2')
GENERIC_INIT: Template  = templates.get_template('generic_init.py.j2')
PACKAGE_INIT: Template  = templates.get_template('package_init.py.j2')
SERVICE_INIT: Template  = templates.get_template('service_init.py.j2')
DATA_TYPE: Template     = templates.get_template('data_type.py.j2')
OVERRIDES: Template     = templates.get_template('overrides.py.j2')
