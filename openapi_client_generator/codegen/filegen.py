""" Generates client file structure
"""
from string import digits
from pathlib import Path
from typing import NamedTuple, Mapping

from inflection import underscore
import openapi_type as oas

from . import templates


README = Path('README.txt')
MANIFEST = Path('MANIFEST.in')
SETUP_PY = Path('setup.py')
REQUIREMENTS = Path('requirements') / 'minimal.txt'


class Binding(NamedTuple):
    layout: Path
    template: templates.Template


class ProjectLayout(NamedTuple):
    root: Path
    client_root: Path
    endpoints: Mapping[Binding, oas.PathItem]
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
    name = underscore(name)
    client_root = root / name
    endpoints_root = client_root / "service"

    endpoints = {}
    for path, item in spec.paths.items():
        pth = api_path_to_filepath(path)
        endpoints[Binding(endpoints_root / pth, templates.ENDPOINT)] = item

    return ProjectLayout(
        root=root,
        client_root=client_root,
        readme=Binding(root / README, templates.README),
        manifest=Binding(root / MANIFEST, templates.MANIFEST),
        setup_py=Binding(root / SETUP_PY, templates.SETUP_PY),
        requirements=Binding(root / REQUIREMENTS, templates.REQUIREMENTS),
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
    print('Done.')
