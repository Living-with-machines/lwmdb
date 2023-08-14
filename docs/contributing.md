# Contributing

Please see our [Code of Conduct](code_of_conduct.md) for policies on contributing. We also broadly follow the [Turing Way Code of Conduct](https://the-turing-way.netlify.app/community-handbook/coc.html) to encourage a pleasant experience contributing and collaborating on this project.

## Documentation

If you would only like to contribute to documentation, the easiest way to deploy and see changes rendered with each edit is to run *outside* docker:

```console
$ git clone https://github.com/living-with-machines/lwmdb
$ cd lwmdb
$ poetry install --with dev --with docs
$ poetry run mkdocs serve --dev-addr=0.0.0.0:8080
```

!!! note

    The `--with dev` and `--with docs` options are currently included by default, but they may be set as optional in the future.

Documentation should also be available on `https://localhost:9000` when running 

```console
docker compose -f local.yml up
```

but it does *not* auto update as local changes are made. Port `8080` is specified in the example above to avoid conflict with a local `docker compose` run (which defaults to `0.0.0.0:9000`).

!!! warning

    The [`schema`](advanced/schema.md) currently raises an error. See ticket [`#115`](https://github.com/Living-with-machines/lwmdb/issues/115) for updates.

## Local `docker` test runs

### Local environment

Tests are built and run via [`pytest`](https://docs.pytest.org/) and `docker` using [`pytest-django`](https://pytest-django.readthedocs.io/en/latest/). To run tests ensure a local `docker` install, a local `git` checkout of `lwmdb` and a build (see [install instructions](install.md) for details).

Running locally with `local.yml` in a terminal deploys the site and this documentation:

=== "user"

    ```console
    docker compose -f local.yml up
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml up
    ```

- Site at `localhost:3000`
- Docs at `localhost:9000`

!!! note

    If there are issues starting the server, shutting it down and then starting up again may help 

    === "user"

        ```console
        docker compose -f local.yml down
        ```

    === "sudo"

        ```console
        sudo docker compose -f local.yml down
        ```

### Running tests

To run tests, open another terminal to run `pytest` within the `django` `docker` `container` while `docker` is running. 

=== "user"

    ```console
    docker compose -f local.yml exec django pytest
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml exec django pytest
    ```

These will print out a summary of test results like:

```pytest
Test session starts (platform: linux, Python 3.11.3, pytest 7.3.1, pytest-sugar 0.9.7)
django: settings: config.test_settings (from ini)
rootdir: /app
configfile: pyproject.toml
plugins: pyfakefs-5.2.2, anyio-3.6.2, sugar-0.9.7, cov-4.0.0, django-4.5.2
collected 33 items / 1 deselected / 32 selected

 gazetteer/tests.py ✓                                          3% ▍
 lwmdb/tests/test_commands.py xx                               9% ▉
 mitchells/tests.py x✓                                       100% ██████████
 newspapers/tests.py ✓✓✓✓✓                                    28% ██▊
 lwmdb/utils.py ✓✓✓✓✓✓✓✓✓                                     56% █████▋
 lwmdb/tests/test_utils.py ✓✓✓✓✓✓✓✓✓✓✓✓✓                      97% █████████▊
------------ coverage: platform linux, python 3.11.3-final-0 ---------------
Name                                                     Stmts   Miss  Cover
----------------------------------------------------------------------------
lwmdb/management/commands/connect.py                        10      3    70%
lwmdb/management/commands/createfixtures.py                 42     30    29%
lwmdb/management/commands/fixtures.py                      126     78    38%
lwmdb/management/commands/load_json_fixtures.py             20     11    45%
lwmdb/management/commands/loadfixtures.py                   27      8    70%
lwmdb/management/commands/makeitemfixtures.py               78     62    21%
lwmdb/tests/test_commands.py                                15      2    87%
lwmdb/tests/test_utils.py                                   25      7    72%
lwmdb/utils.py                                             120     48    60%
----------------------------------------------------------------------------
TOTAL                                                      508    284    44%

8 files skipped due to complete coverage.

============================ slowest 3 durations ===========================
3.85s setup    gazetteer/tests.py::TestGeoSpatial::test_create_place_and_distance
1.06s call     lwmdb/tests/test_commands.py::test_mitchells
0.14s call     lwmdb/utils.py::lwmdb.utils.download_file

Results (6.74s):
      29 passed
       3 xfailed
       1 deselected
```

### Adding all expected failed tests

In the previous example, 29 tests passed, 3 failed *as expected* (hence `xfailed`) and 1 test was skipped (`deselected`). To see the deatils of what tests failed, adding the `--runxfail` option will add reports like the following:  

=== "user"

    ```console
    docker compose -f local.yml exec django pytest --runxfail
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml exec django pytest --runxfail
    ```

```pytest
...
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
E       AttributeError: 'Series' object has no attribute 'NLP'

/usr/local/lib/python3.11/site-packages/pandas/core/generic.py:5989: AttributeError
-------------------------- Captured stdout call ----------------------------
Warning: Model mitchells.Issue is missing a fixture file and will not load.
Warning: Model mitchells.Entry is missing a fixture file and will not load.
Warning: Model mitchells.PoliticalLeaning is missing a fixture file and will not load.
Warning: Model mitchells.Price is missing a fixture file and will not load.
Warning: Model mitchells.EntryPoliticalLeanings is missing a fixture file and will not load.
Warning: Model mitchells.EntryPrices is missing a fixture file and will not load.

 lwmdb/tests/test_commands.py ⨯                           6% ▋
...
```

and summaries at the end of the report

```pytest
...
============================ slowest 3 durations ===========================
3.87s setup    gazetteer/tests.py::TestGeoSpatial::test_create_place_and_distance
1.07s call     lwmdb/tests/test_commands.py::test_mitchells
0.15s call     lwmdb/utils.py::lwmdb.utils.download_file
========================== short test summary info =========================
FAILED lwmdb/tests/test_commands.py::test_mitchells - AttributeError: 'Series' object
has no attribute 'NLP'
FAILED lwmdb/tests/test_commands.py::test_gazzetteer - SystemExit: App(s) not allowed: ['gazzetteer']
FAILED mitchells/tests.py::MitchelsFixture::test_load_fixtures - assert 0 > 0

Results (6.90s):
      29 passed
       3 failed
         - lwmdb/tests/test_commands.py:9 test_mitchells
         - lwmdb/tests/test_commands.py:19 test_gazzetteer
         - mitchells/tests.py:18 MitchelsFixture.test_load_fixtures
       1 deselected
```

### Terminal Interaction

Adding the `--pdb` option generates an `ipython` shell at the point a test fails:

=== "user"

    ```console
    docker compose -f local.yml exec django pytest --runxfail --pdb
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml exec django pytest --runxfail --pdb
    ```


```pytest
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
E       AttributeError: 'Series' object has no attribute 'NLP'

/usr/local/lib/python3.11/site-packages/pandas/core/generic.py:5989: AttributeError
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> entering PDB >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

>>>>>>>>>>>>>>>> PDB post_mortem (IO-capturing turned off) >>>>>>>>>>>>>>>>>
> /usr/local/lib/python3.11/site-packages/pandas/core/generic.py(5989)__getattr__()
   5987         ):
   5988             return self[name]
-> 5989         return object.__getattribute__(self, name)
   5990
   5991     def __setattr__(self, name: str, value) -> None:

ipdb>
```


## Development

### Commits

#### Pre-commit

The `.pre-commit-config.yaml` file manages configurations to ensure quality of each `git` commit. Ensure this works by installing [`pre-commit`](https://pre-commit.com/#install) before making any `git` commits.

!!! note

    `pre-commit` is included in the `pyproject.toml` `dev` dependencies group, so it's possible to run all `git` commands within a local `poetry` install of `lwmdb` without installing `pre-commit` globally.   

This will automatically download and install dependencies specified in `.pre-commit-config.yaml` and then run all those checks for any `git` commit.

You can run all of these checks outside a commit with

=== "shell"

    ```console
    pre-commit run --all-files
    ```

=== "poetry"

    ```console
    poetry run pre-commit run --all-files
    ```

#### Commit messages

For git commit messages we try to follow the [`conventional commits`](https://www.conventionalcommits.org/en/v1.0.0/) spec, where commits are prefixed by categories:

- `fix`: something fixed
- `feat`: a new feature
- `doc`: documentation
- `refactor`: a significant rearangement code structure
- `test`: adding tests
- `ci`: continuous integrations
- `chore`: something relatively small like updating a dependency
 

### App

Once `docker compose` is up, any local modifications should automatically be loaded in the local `django` `docker` `container` and immediately applied. This suits reloading web app changes (including `css` etc.) and writing and running tests. No additional `docker build` commands *should* be required unless very significant modifcations, such as shifting between `git` `branches`.

### Tests

#### Doctests

Including `docstrings` with example tests is an efficient way to add tests, document usage and help ensure documentation is consistent with code changes.

#### Pytest Tests

We use [`pytest`](https://docs.pytest.org/) for tests, and their documentation is quite comprehensive. The [`django-pytest`](https://pytest-django.readthedocs.io/en/latest/) module is crucial to the test functionality as well.

##### Pytest Configuration

The config for running tests is shared between `pyproject.toml` and `lwmdb/tests/conftest.py`.

The `pyproject.toml` section below provides automatic test configuration whenever `pytest` is run. An example config at the time of this writing:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.test_settings"
python_files = ["tests.py", "test_*.py"]
addopts = """
--cov=lwmdb
--cov-report=term:skip-covered
--pdbcls=IPython.terminal.debugger:TerminalPdb
--doctest-modules
--ignore=compose
--ignore=jupyterhub_config.py
--ignore=notebooks
--ignore=docs
--ignore=lwmdb/contrib/sites
-m "not slow"
--durations=3
"""
markers = [
  "slow: marks tests as slow (deselect with '-m \"not slow\"')"
]
```

- `--cov=lwmdb` specifies the path to test (in this case the name of this project)
- `--cov-report=term:skip-covered` excludes files with full coverage from the coverage report
- `--pydbcls=Ipython.terminal.debugger:TerminalPdb` enables the `ipython` terminal for [debugging ](https://ipython.readthedocs.io/en/stable/api/generated/IPython.core.debugger.html)
- `--doctest-modules` indicates `doctests` are included in test running
- `--ignore` excludes folders from testing (eg: `--ignore=compose` skips the `compose` folder)
- `-m "not slow"` skips tests [marked](https://docs.pytest.org/en/latest/how-to/mark.html) with `@pytest.mark.slow`
- `--duration=3` lists the duration of the 3 slowest running tests

##### Example Tests

Within each `django` `app` in the project there is either a `tests.py` file or a `tests` folder, where any file name beginning with `test_` is included (like `test_commands.py`).

An example test from `mitchells/tests.py`:

```python 
{%
   include "../mitchells/tests.py"
   start="# Example for Contributing docs"
%}
```

<!-- Here the `remote_data` `mark` indicates that this test will fail without a working internet connection (in this case dowloading a remote file). Assuming that is available, the -->
`mitchells_data_path` [`fixture`](https://docs.pytest.org/en/stable/explanation/fixtures.html) is defined in `conftest.py` and returns a `Path` for the folder where raw `mitchells` data is stored prior to processing into `json`.

`Fixtures` in `pytest` work by automatically populating any functions names beginning with `test_` with whatever is returned from registered `fixture` functions. Here the `mitchells_data_path` `Path` object is passed to the `download_file` function and saved to `MITCHELLS_LOCAL_LINK_EXCEL_URL`. `download_file` returns a `bool` to indicate if the dowload was successful, hence then testing if the value returned is `True` via the line:

```python
assert success
```

The lines involving `caplog` aid testing `logging`. The [logging level](https://docs.python.org/3/library/logging.html#logging-levels) is to `INFO` to capture levels lower than the default `WARNING` level.

```python
caplog.set_level(INFO)
```

This then means the logging is captured and can be tested on the final line 

```python
assert caplog.messages == [
    f'{MITCHELLS_LOCAL_LINK_EXCEL_PATH} file available from {mitchells_data_path}'
]
```

!!! note

    To ease using `python` logging and `django` logging features we use our [`log_and_django_terminal`](reference/lwmdb/utils.md#lwmdb.utils.log_and_django_terminal) wrapper to ease managing logs that might also need to be printed at the terminal alongside commands.


## Crediting Contributions

We use `allcontributors` to help mmanage attributing contributions to both this code base and to portions of the datasets we release for use with `lwmdb`.

### [All Contributors][allcontributors.org]

All Contributors is a service for managing credit to a `git` repository. `.all-contributorsrc` is a `json` file in the root directory of the `alnm` repository. It includes basic display configuration for what's printed in `README.md` and the intro to this documentation. 

The `json` structure follows this [`format`](https://allcontributors.org/docs/en/specification). This has the following format:

```json
{
  "files": [
    "README.md"
  ],
  "imageSize": 100,
  "commit": false,
  "commitType": "docs",
  "commitConvention": "angular",
  "contributors": [
    {
      "login": "github-user-name",
      "name": "Person Name",
      "avatar_url": "https://avatars.githubusercontent.com/u/1234567?v=4",
      "profile": "http://www.a-website.org",
      "contributions": [
        "code",
        "ideas",
        "doc"
      ]
    },
    {
      "login": "another-github-user-name",
      "name": "Another Name",
      "avatar_url": "https://avatars.githubusercontent.com/u/7654321?v=4",
      "contributions": [
        "code",
        "ideas",
        "doc",
        "maintenance"
      ]
    },
  ],
  "contributorsPerLine": 7,
  "skipCi": true,
  "repoType": "github",
  "repoHost": "https://github.com",
  "projectName": "lwmdb",
  "projectOwner": "Living-with-machines"
}
```

This provides helps credit contributions and formatting for rendering a contributors grid of profiles in markdown. 

The `contribution` component covers at least these categories for `lwmdb`. 

- `code`
- `ideas`
- `mentoring`
- `maintenance`
- `doc`

At present we aren't considered other code contribtuiontypes. For more detailed examples provided by `allcontributors` by default, see the [`emoji-key` table](https://allcontributors.org/docs/en/emoji-key#table). 

#### Adding credit, including types, via GitHub comments

A `github` user with at least [`moderator`](https://docs.github.com/en/organizations/managing-peoples-access-to-your-organization-with-roles/managing-moderators-in-your-organization) permission should be able to post to an `lwmdb` `github` ticket in the following form:

```markdown
@all-contributors
please add @github-user for code, ideas, planning.
please add @github-other-user for code, ideas, planning.
```

which should cause the [`all-contributors bot`](https://github.com/all-contributors/app) to indicated success:

```markdown
@AoifeHughes

I've put up a pull request to add @github-user! 🎉
I've put up a pull request to add @github-other-user! 🎉
```

or indicate errors

```markdown
This project's configuration file has malformed JSON: .all-contributorsrc. Error:: Unexpected token : in JSON at position 2060
```


### CITATION.CFF

We also maintain a [`Citation File Format (CFF)`](`cff-version`) for citeable, academic credit for contributions via our [`zenodo`](10.5281/zenodo.8208203) registration. This helps automate the process of releasing citation Digital Object Identifyer (DOI) codes, alongside version releases of `lwmdb`.

`CFF` supports Open Researcher and Contributor ID (`orcid`)[https://en.wikipedia.org/wiki/ORCID], which eases automating academic credit for evolving contribtuions to academic work. In this case we endeavour to harmonise contributions recorded via `allcontributors` with input from collaborators across [Living with Machines](https://livingwithmachines.ac.uk/) who have contributed to `lwmdb`.

For reference a simplified example based on `cff-version 1.2.0`:

```yaml
cff-version: 1.2.0
title: Living With Machines Database
message: >-
  If you use this software, please cite it using the
  metadata from this file.
type: software
authors:
  - given-names: Person
    family-names: Name
    orcid: 'https://orcid.org/0000-0000-0000-0000'
    affiliation: A UNI
  - given-names: Another
    family-names: Name
    orcid: 'https://orcid.org/0000-0000-0000-0001'
    affiliation: UNI A
identifiers:
  - type: doi
    value: 10.5281/zenodo.8208204
repository-code: 'https://github.com/Living-with-machines/lwmdb'
url: 'https://livingwithmachines.ac.uk/'
license: MIT
```

## Troubleshooting

### Unexpected `lwmdb/static/css/project.css` changes

At present (see issue [#110](https://github.com/Living-with-machines/lwmdb/issues/110) for updates) running `docker compose` is likely to truncate the last line of `/lwmdb/static/css/project.css` which, can then appear as a local change in a `git` checkout:

```git-console
$ git status
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   lwmdb/static/css/project.css
```

This should be automatically fixed via [`pre-commit`](#pre-commit), and if necessary you can run `pre-commit` directly to clean that issue outside of a `git` commit. Given how frequently this may occur, it is safest to simply leave that until commiting a change.

=== "shell"

    ```console
    pre-commit run --all-files
    ```

=== "poetry"

    ```console
    poetry run pre-commit run --all-files
    ```
