from jinja2 import Environment, PackageLoader


env = Environment(
    loader=PackageLoader('openapi-client-generator', 'templates')
)
