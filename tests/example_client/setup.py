from pathlib import Path
from setuptools import setup
from setuptools import find_packages


here = Path(__file__).absolute().parent


EXTRAS = frozenset({
})


def extras_require(all_extras=EXTRAS):
    """ Get map of all extra requirements
    """
    return {
        x: requirements(here / 'requirements' / 'extras' / f'{x}.txt') for x in all_extras
    }


def requirements(at_path: Path):
    with at_path.open() as f:
        rows = f.read().strip().split('\n')
        requires = []
        for row in rows:
            row = row.strip()
            if row and not (row.startswith('#') or row.startswith('http')):
                requires.append(row)
    return requires


with (here / 'README.md').open() as f:
    README = f.read()


# Setup
# ----------------------------

setup(name='example-client',
      version='0.0.1',
      description='OpenAPI Client',
      long_description=README,
      classifiers=[
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
      ],
      author='openapi-client-generator',
      url='https://github.com/avanov/openapi-client-generator',
      keywords='openapi oas swagger schema serialization deserialization structured-data http client',
      packages=find_packages(exclude=['tests', 'tests.*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requirements(here / 'requirements' / 'minimal.txt'),
      extras_require=extras_require(),
    )