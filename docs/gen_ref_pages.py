"""Generate documentation pages from docstrings."""

from logging import getLogger
from pathlib import Path
from typing import Generator

import mkdocs_gen_files

logger = getLogger(__name__)


CODE_PATH: str = "."
CODE_DOC_REGEX: str = "*.py"
DOC_SUFFIX: str = ".md"
GEN_DOC_PATH: str = "reference"
DOC_NAV_FILE_NAME: str = "DOC_STRINGS.md"
DOC_NAV_FILE_PATH: Path = Path(str(GEN_DOC_PATH)) / str(DOC_NAV_FILE_NAME)

EXCLUDE_PATHS: tuple[str, ...] = (
    "jupyterhub_config.js",
    ".ipynb_checkpoints",
    "migrations",
    "manage",
    "docs",
    "site",
    "staticfiles",
    "backups",
    "fixture-files",
    "metadata",
    "tests",
)
IPYNB_PATH: str = ".ipynb_checkpoints"

nav = mkdocs_gen_files.Nav()


for path in sorted(Path(str(CODE_PATH)).rglob(CODE_DOC_REGEX)):
    module_path: Path = path.relative_to(str(CODE_PATH)).with_suffix("")
    doc_path: Path = path.relative_to(str(CODE_PATH)).with_suffix(DOC_SUFFIX)

    full_doc_path: Path = Path(str(GEN_DOC_PATH), doc_path)

    parts: tuple[str, ...] = tuple(module_path.parts)
    logger.debug(f"Managing module path {parts}")

    if parts[-1] == "__init__":
        parts = parts[:-1]
        if len(parts) == 0:
            logger.debug(f"Skipping {parts}")
            continue
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__" or set(EXCLUDE_PATHS) & set(parts):
        logger.debug(f"Skipping module path {parts}")
        continue

    logger.debug(f"Will write to {full_doc_path}")

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        doc_md_path: str = ".".join(parts)
        section_heading: str = "::: " + doc_md_path
        logger.debug(f"Adding {section_heading}")
        fd.write(section_heading)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)


with mkdocs_gen_files.open(DOC_NAV_FILE_PATH, "w") as nav_file:
    logger.warning(f"Opening {DOC_NAV_FILE_NAME} to generate navigation file.")
    literate_nav_str: Generator = nav.build_literate_nav()
    logger.debug(f"Writing:\n{literate_nav_str}")
    nav_file.writelines(literate_nav_str)
