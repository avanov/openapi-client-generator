""" Generates client file structure
"""
from itertools import chain
from pathlib import Path
from shutil import copytree
from typing import NamedTuple, Mapping, Generator, Tuple, Iterable, Union
from pkg_resources import get_distribution

from inflection import underscore
import openapi_type as oas

from . import templates
from ..info import DISTRIBUTION_NAME, PACKAGE_NAME
from ..transformers import SpecMeta, openapi_to_codegen_metadata


README       = Path('README.md')
MANIFEST     = Path('MANIFEST.in')
SETUP_PY     = Path('setup.py')
REQUIREMENTS = Path('requirements') / 'minimal.txt'


class EmptyContext(NamedTuple):
    pass


class EndpointContext(NamedTuple):
    package_name: str
    endpoint_url: str
    params_type: str
    request_type: str
    response_type: str
    headers_type: str


class ServiceContext(NamedTuple):
    import_names: Iterable[str]


class ReadmeContext(NamedTuple):
    client_name: str


class ManifestContext(NamedTuple):
    package_name: str


class SetupContext(NamedTuple):
    client_name: str


EMPTY_CONTEXT = EmptyContext()


Context = Union[ EndpointContext
               , ServiceContext
               , ReadmeContext
               , ManifestContext
               , SetupContext
               , EmptyContext ]


class Binding(NamedTuple):
    layout: Path
    template: templates.Template
    context: Context


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
    meta = openapi_to_codegen_metadata(spec)
    py_name = underscore(name)
    client_root = root / py_name
    endpoints_root = client_root / "service"
    common_root = client_root / "common"

    endpoints = endpoints_bindings(meta, py_name, endpoints_root)

    return ProjectLayout(
        root=root,
        client_root=client_root,
        common_root=common_root,
        endpoints_root=endpoints_root,
        readme=Binding(
            root / README, templates.README, ReadmeContext(client_name=name,)
        ),
        manifest=Binding(root / MANIFEST, templates.MANIFEST, ManifestContext(package_name=py_name)),
        setup_py=Binding(root / SETUP_PY, templates.SETUP_PY, SetupContext(client_name=name)),
        requirements=Binding(root / REQUIREMENTS, templates.REQUIREMENTS, EMPTY_CONTEXT),
        endpoints=endpoints
    )


def endpoints_bindings(meta: SpecMeta, package_name: str, endpoints_root: Path) -> Endpoints:
    endpoints = {}
    for pth, item in meta.paths.items():
        for name, method in _iter_supported_methods(item):
            target = endpoints_root / pth / f'{name}.py'
            ctx = EndpointContext(
                package_name=package_name,
                endpoint_url='undefined',
                params_type=templates.PARAMS_TYPE.render({}),
                request_type=templates.REQUEST_TYPE.render({}),
                response_type=templates.RESPONSE_TYPE.render({}),
                headers_type=templates.HEADERS_TYPE.render({}),
            )
            endpoints[Binding(target, templates.ENDPOINT, ctx)] = method
            # make sure there's __init__ in every sub-package
            for sub_pkg in (x for x in target.parents if x > endpoints_root):
                endpoints[Binding(sub_pkg / '__init__.py', templates.ENDPOINT_INIT, EMPTY_CONTEXT)] = method
    return endpoints


def generate_from_layout(l: ProjectLayout) -> None:
    for binding in [l.readme, l.manifest, l.setup_py, l.requirements]:
        _generate_file(binding)
    _generate_file(Binding(l.client_root / '__init__.py', templates.PACKAGE_INIT, EMPTY_CONTEXT))
    _copy_common_library(l.common_root)
    _generate_endpoints(l.endpoints)
    _generate_imports(l.endpoints_root)


def _generate_endpoints(e: Endpoints) -> None:
    for py_binding, data in e.items():
        _generate_file(py_binding)


def _generate_imports(root: Path, init_name: str = '__init__.py') -> None:
    for init in chain(root.rglob(init_name), [root / init_name]):
        import_names = (mod.name.replace('.py', '') for mod in init.parent.iterdir() if mod.name != init_name)
        ctx = ServiceContext(import_names=import_names)._asdict()
        with init.open('w') as f:
            templates.SERVICE_INIT.stream(ctx).dump(f)


def _generate_file(binding: Binding) -> None:
    if not binding.layout.parent.exists():
        binding.layout.parent.mkdir(exist_ok=True, parents=True)
    binding.layout.touch(exist_ok=False)
    with binding.layout.open('w') as f:
        binding.template.stream(binding.context._asdict()).dump(f)


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
