""" Generates client file structure
"""
from itertools import chain
from pathlib import Path
from shutil import copytree
from typing import NamedTuple, Mapping, Iterable, Union
from pkg_resources import get_distribution

from inflection import underscore
import openapi_type as oas
import black
from pyrsistent import pmap
from pyrsistent.typing import PMap

from . import templates
from ..info import DISTRIBUTION_NAME, PACKAGE_NAME
from ..common.types import AttrStyle
from ..transformers import SpecMeta, openapi_to_codegen_metadata, EndpointMethod, ResolvedTypesMap, TypeContext, \
    ResolvedTypesVec

README       = Path('README.md')
MANIFEST     = Path('MANIFEST.in')
SETUP_PY     = Path('setup.py')
REQUIREMENTS = Path('requirements') / 'minimal.txt'


class EmptyContext(NamedTuple):
    pass


class EndpointContext(NamedTuple):
    package_name: str
    endpoint_url: str
    path_params_type: str
    query_type: str
    request_type: str
    response_type: str
    headers_type: str
    request_style: AttrStyle
    query_style: AttrStyle
    response_is_stream: bool
    request_overrides: str
    response_overrides: str
    query_overrides: str


class ServiceContext(NamedTuple):
    import_names: Iterable[str]


class ReadmeContext(NamedTuple):
    client_name: str
    package_name: str


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


Endpoints = Mapping[Binding, EndpointMethod]


class ProjectLayout(NamedTuple):
    root: Path
    client_root: Path
    endpoints_root: Path
    common_root: Path
    common_types: ResolvedTypesVec
    endpoints: Endpoints
    readme: Binding
    manifest: Binding
    setup_py: Binding
    requirements: Binding
    query_style: AttrStyle
    request_style: AttrStyle


def get_project_layout(
    spec: oas.OpenAPI,
    root: Path,
    name: str,
    query_style: AttrStyle,
    request_style: AttrStyle,
) -> ProjectLayout:
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

    endpoints = endpoints_bindings(meta, py_name, endpoints_root, request_style, query_style)

    return ProjectLayout(
        root=root,
        client_root=client_root,
        common_root=common_root,
        common_types=meta.common_types,
        endpoints_root=endpoints_root,
        readme=Binding(
            root / README, templates.README, ReadmeContext(
                client_name=name,
                package_name=py_name,
            )
        ),
        manifest=Binding(root / MANIFEST, templates.MANIFEST, ManifestContext(package_name=py_name)),
        setup_py=Binding(root / SETUP_PY, templates.SETUP_PY, SetupContext(client_name=name)),
        requirements=Binding(root / REQUIREMENTS, templates.REQUIREMENTS, EMPTY_CONTEXT),
        endpoints=endpoints,
        query_style=query_style,
        request_style=request_style,
    )


def endpoints_bindings(
    meta: SpecMeta,
    package_name: str,
    endpoints_root: Path,
    request_style: AttrStyle,
    query_style: AttrStyle,
) -> Endpoints:
    endpoints = {}
    for pth, item in meta.paths.items():
        for method in item.supported_methods:
            target = endpoints_root / pth.as_fs_path() / f'{method.name}.py'
            query_types_overrides: PMap[str, str] = pmap()
            for qt in method.query_types:
                query_types_overrides = query_types_overrides.update(qt.overrides)
            ctx = EndpointContext(
                package_name=package_name,
                endpoint_url=pth.as_endpoint_url(),
                path_params_type=render_type_context(method.path_params_type),
                headers_type='\n\n'.join(render_type_context(x) for x in method.headers_types),
                query_type='\n\n'.join(render_type_context(x) for x in method.query_types),
                request_type='\n\n'.join(render_type_context(x) for x in method.request_types),
                response_type='\n\n'.join(render_type_context(x) for x in method.response_types),
                request_style=request_style,
                query_style=query_style,
                response_is_stream=method.response_is_stream,

                request_overrides=templates.OVERRIDES.render({
                    'overrides': {}
                }).strip(),
                response_overrides=templates.OVERRIDES.render({
                    'overrides': {}
                }).strip(),
                query_overrides=templates.OVERRIDES.render({
                    'overrides': query_types_overrides
                }).strip(),
            )
            endpoints[Binding(target, templates.ENDPOINT, ctx)] = method
            # make sure there's `__init__.py` in every sub-package
            for sub_pkg in (x for x in target.parents if x > endpoints_root):
                endpoints[Binding(sub_pkg / '__init__.py', templates.ENDPOINT_INIT, EMPTY_CONTEXT)] = method
    return endpoints


def generate_from_layout(l: ProjectLayout) -> None:
    for binding in [l.readme, l.manifest, l.setup_py, l.requirements]:
        _generate_file(binding)
    _generate_file(Binding(l.client_root / '__init__.py', templates.PACKAGE_INIT, EMPTY_CONTEXT))
    _copy_common_library(l.common_root)
    _generate_common_types(l.common_root, l.common_types)
    _generate_endpoints(l.endpoints)
    _generate_imports(l.endpoints_root)
    _mark_as_typed(l.client_root)
    _code_style(l.client_root)


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


def _generate_common_types(common_root: Path, common_types: ResolvedTypesVec) -> None:
    processed = set()  # TODO: discover why duplicates exist
    with (common_root / 'types.py').open('a') as f:
        for typ in common_types:
            if typ in processed:
                continue
            processed.add(typ)
            f.write('\n')
            f.write(render_type_context(typ))
            f.write('\n\n')



def render_type_context(t: TypeContext) -> str:
    return templates.DATA_TYPE.render({x: getattr(t, x) for x in chain(t._fields, ['ordered_attrs', 'common_reference_render'])}).strip()


def _mark_as_typed(dir: Path) -> None:
    (dir / 'py.typed').touch(mode=0o644, exist_ok=False)


def _code_style(dir: Path) -> None:
    for file in dir.rglob('**/*.py'):
        black.format_file_in_place(
            src=file.absolute(),
            fast=False,
            mode=black.Mode(
                line_length=100,
                target_versions={black.TargetVersion.PY38}
            ),
            write_back=black.WriteBack.YES
        )
