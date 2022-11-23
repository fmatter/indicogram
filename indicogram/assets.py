from pathlib import Path

from clld.web.assets import environment

import indicogram

environment.append_path(
    Path(indicogram.__file__).parent.joinpath("static").as_posix(),
    url="/indicogram:static/",
)
environment.load_path = list(reversed(environment.load_path))
