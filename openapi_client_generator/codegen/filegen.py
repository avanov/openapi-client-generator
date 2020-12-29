""" Generates client file structure
"""
from itertools import chain
from string import digits
from pathlib import Path
from shutil import copytree
from typing import NamedTuple, Mapping, Any, Generator, Tuple
from pkg_resources import get_distribution

from pyrsistent import pmap
from inflection import underscore
import openapi_type as oas

from . import templates
from ..info import DISTRIBUTION_NAME, PACKAGE_NAME


README = Path('README.md')
MANIFEST = Path('MANIFEST.in')
SETUP_PY = Path('setup.py')
REQUIREMENTS = Path('requirements') / 'minimal.txt'

EMPTY_CONTEXT: Mapping[str, Any] = pmap()


class Binding(NamedTuple):
    layout: Path
    template: templates.Template
    context: Mapping[str, Any]


Endpoints = Mapping[Binding, oas.Operation]


class ProjectLayout(NamedTuple):
    root: Path
    client_root: Path
    endpoints_root: Path
    common_root: Path
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
    common_root = client_root / "common"

    endpoints = endpoints_bindings(spec, py_name, endpoints_root)

    return ProjectLayout(
        root=root,
        client_root=client_root,
        common_root=common_root,
        endpoints_root=endpoints_root,
        readme=Binding(root / README, templates.README, {
            'client_name': name,
            'client_caption_separator': '=' * len(name),
        }),
        manifest=Binding(root / MANIFEST, templates.MANIFEST, {'package_name': py_name}),
        setup_py=Binding(root / SETUP_PY, templates.SETUP_PY, {'client_name': name}),
        requirements=Binding(root / REQUIREMENTS, templates.REQUIREMENTS, EMPTY_CONTEXT),
        endpoints=endpoints
    )


def endpoints_bindings(spec: oas.OpenAPI, package_name: str, endpoints_root: Path) -> Endpoints:
    endpoints = {}
    for path, item in spec.paths.items():
        pth = api_path_to_filepath(path)
        for name, method in _iter_supported_methods(item):
            target = endpoints_root / pth / f'{name}.py'
            endpoints[Binding(target, templates.ENDPOINT, pmap({'package_name': package_name}))] = method
            # make sure there's __init__ in every sub-package
            for sub_pkg in (x for x in target.parents if x > endpoints_root):
                endpoints[Binding(sub_pkg / '__init__.py', templates.ENDPOINT_INIT, EMPTY_CONTEXT)] = method
    return endpoints


def api_path_to_filepath(api_path: str, sep: str = '/') -> Path:
    """
    :param api_path: URL path
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
    rv = underscore(''.join(final))
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
    _generate_file(Binding(l.client_root / '__init__.py', templates.PACKAGE_INIT, {}))
    _copy_common_library(l.common_root)
    _generate_endpoints(l.endpoints)
    _generate_imports(l.endpoints_root)


def _generate_endpoints(e: Endpoints) -> None:
    for py_binding, data in e.items():
        _generate_file(py_binding)


def _generate_imports(root: Path) -> None:
    init_name = '__init__.py'
    for init in chain(root.rglob(init_name), [root / init_name]):
        import_names = (mod.name.replace('.py', '') for mod in init.parent.iterdir() if mod.name != init_name)
        with init.open('w') as f:
            templates.SERVICE_INIT.stream({
                'import_names': import_names
            }).dump(f)


def _generate_file(binding: Binding) -> None:
    if not binding.layout.parent.exists():
        binding.layout.parent.mkdir(exist_ok=True, parents=True)
    binding.layout.touch(exist_ok=False)
    with binding.layout.open('w') as f:
        binding.template.stream(binding.context).dump(f)


def _copy_common_library(common_root: Path) -> None:
    dist = get_distribution(DISTRIBUTION_NAME)
    copytree(str(Path(dist.location) / PACKAGE_NAME / 'common'), str(common_root))


def _iter_supported_methods(path: oas.PathItem) -> Generator[Tuple[str, oas.Operation], None, None]:
    methods = (path.head,
               path.get,
               path.post,
               path.put,
               path.patch,
               path.delete,
               path.trace)
    for name, method in path._asdict().items():
        if not method or method not in methods:
            continue
        yield name, method
