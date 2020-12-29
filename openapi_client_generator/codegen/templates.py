from jinja2 import Environment, PackageLoader, Template, StrictUndefined


templates = Environment(
    loader=PackageLoader('openapi_client_generator', 'templates'),
    undefined=StrictUndefined  # raise exception on missing variables
)


README: Template       = templates.get_template('README.rst.j2')
MANIFEST: Template     = templates.get_template('MANIFEST.in.j2')
SETUP_PY: Template     = templates.get_template('setup.py.j2')
REQUIREMENTS: Template = templates.get_template('requirements.txt.j2')
ENDPOINT: Template     = templates.get_template('endpoint.py.j2')
