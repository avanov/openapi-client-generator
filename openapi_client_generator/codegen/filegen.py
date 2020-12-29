""" Generates client file structure
"""
from inflection import underscore
from pathlib import Path
from typing import NamedTuple, Mapping, Generator

import openapi_type as oas


README = Path('README.txt')
MANIFEST = Path('MANIFEST.in')
SETUP_PY = Path('setup.py')


class ProjectLayout(NamedTuple):
    root: Path
    client_root: Path
    endpoints: Mapping[Path, oas.PathItem]
    readme: Path
    manifest: Path
    setup_py: Path


def client_layout(spec: oas.OpenAPI, root: Path, name: str) -> ProjectLayout:
    """
    :param spec: parsed OpenAPI Spec
    :param root: client root path
    :param name: client python package name
    :return:
    """
    name = underscore(name)
    client_root = root / name
    endpoints_root = client_root / "service"

    endpoints = {}
    for path, item in spec.paths.items():
        pth = api_path_to_filepath(path)
        endpoints[endpoints_root / pth] = item

    return ProjectLayout(
        root=root,
        client_root=client_root,
        readme=root / README,
        manifest=root / MANIFEST,
        setup_py=root / SETUP_PY,
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
        try:
            _ = int(rv)
        except ValueError:
            pass
        else:
            rv = f'v{rv}'
    return rv

