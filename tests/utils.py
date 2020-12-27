from pathlib import Path
import json
from openapi_client_generator.oas_spec import Specification, parse_spec


def load_spec(s: Path) -> Specification:
    with s.open() as fd:
        return parse_spec(json.load(fd))
