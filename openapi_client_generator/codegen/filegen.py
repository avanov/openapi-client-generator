""" Generates client file structure
"""
from string import digits
from pathlib import Path
from typing import NamedTuple, Mapping, Any

from pyrsistent import pmap
from inflection import underscore
import openapi_type as oas

from . import templates


README = Path('README.txt')
MANIFEST = Path('MANIFEST.in')
SETUP_PY = Path('setup.py')
REQUIREMENTS = Path('requirements') / 'minimal.txt'

EMPTY_CONTEXT: Mapping[str, Any] = pmap()


class Binding(NamedTuple):
    layout: Path
    template: templates.Template
    context: Mapping[str, Any]


Endpoints = Mapping[Binding, oas.PathItem]


class ProjectLayout(NamedTuple):
    root: Path
    client_root: Path
    endpoints: Endpoints
    readme: Binding
    manifest: Binding
    setup_py: Binding
    requirements: Binding


def client_layout(spec: oas.OpenAPI, root: Path, name: str) -> ProjectLayout:
    """
    :param spec: parsed OpenAPI Spec
    :param root: client root path
    :param name: client python package name
    :return: client layout representation as a type
    """
    py_name = underscore(name)
    client_root = root / py_name
    endpoints_root = client_root / "service"

    endpoints = {}
    for path, item in spec.paths.items():
        pth = api_path_to_filepath(path)
        endpoints[Binding(endpoints_root / pth, templates.ENDPOINT, EMPTY_CONTEXT)] = item

    return ProjectLayout(
        root=root,
        client_root=client_root,
        readme=Binding(root / README, templates.README, EMPTY_CONTEXT),
        manifest=Binding(root / MANIFEST, templates.MANIFEST, {'package_name': name}),
        setup_py=Binding(root / SETUP_PY, templates.SETUP_PY, EMPTY_CONTEXT),
        requirements=Binding(root / REQUIREMENTS, templates.REQUIREMENTS, EMPTY_CONTEXT),
        endpoints=endpoints
    )


def api_path_to_filepath(api_path: str, sep: str = '/') -> Path:
    """
    :param sep: separator symbol used in API path
    """
    segments = [pythonize_path_segment(x) for x in api_path.split(sep) if x.strip()]
    if not segments:
        segments = ['root']
    return Path('/'.join(segments))


def pythonize_path_segment(seg: str) -> str:
    placeholder = {'{', '}'}
    remove = {'.', ','} | placeholder
    is_placeholder = False
    final = []
    for char in seg:
        if char in placeholder:
            is_placeholder = True
            continue
        if char in remove:
            continue
        final.append(char)
    rv = ''.join(final)
    if is_placeholder:
        rv = f'by_{rv}'
    else:
        # version tags are usually numeric
        if rv[0] in digits:
            rv = f'v{rv}'
    return rv


def generate_from_layout(l: ProjectLayout) -> None:
    for binding in [l.readme, l.manifest, l.setup_py, l.requirements]:
        _generate_file(binding)
    _generate_endpoints(l.endpoints)


def _generate_endpoints(e: Endpoints) -> None:
    for py_module, data in e.items():
        print(py_module)


def _generate_file(binding: Binding) -> None:
    binding.layout.parent.mkdir(exist_ok=True)
    binding.layout.touch(exist_ok=False)
    with binding.layout.open('w') as f:
        binding.template.stream(binding.context).dump(f)
