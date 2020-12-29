from jinja2 import Environment, PackageLoader


env = Environment(
    loader=PackageLoader('openapi_client_generator', 'templates')
)
