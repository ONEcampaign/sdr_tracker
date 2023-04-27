from pathlib import Path


class Paths:
    """Class to store the paths to the data and output folders."""

    project = Path(__file__).resolve().parent.parent
    raw_data = project / "raw_data"
    scripts = project / "scripts"
    output = project / "output"
    glossaries = scripts / "glossaries"
