# Living With Machines Database: `lmwdb`

<!-- prettier-ignore-start -->
[![DOI](https://zenodo.org/badge/460939495.svg)](https://zenodo.org/badge/latestdoi/460939495)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Living-with-machines/lwmdb/main.svg)](https://results.pre-commit.ci/latest/github/Living-with-machines/lwmdb/main)

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-13-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
<!-- prettier-ignore-end -->

A package containing database access to the [Living with Machines](https://livingwithmachines.ac.uk/) [newspaper collection](https://livingwithmachines.ac.uk/achievements/)’s metadata, designed to facilitate quicker and easier humanities research on heterogeneous and complex newspaper data.

Background on the development of the database is available in [_Metadata Enrichment in the Living with Machines Project: User-focused Collaborative Database Development in a Digital Humanities Context_](https://zenodo.org/record/8107389) from the [Digital Humanities 2023 book of abstracts](https://zenodo.org/record/7961822).

## Installation

### Install Docker

It is possible to run this code without Docker, but at present we are only maintaining it via Docker Containers so we _highly_ recommend installing Docker to run and/or test this code locally. Instructions are available for most operating systems here: https://docs.docker.com/desktop/

### Clone repository to local drive

Run the following command on your command line:

```console
git clone git@github.com:Living-with-machines/lwmdb.git
```

Followed by:

```console
cd lwmdb
```

### Local deploy of documentation

If you have a local install of [`poetry`](https://python-poetry.org/docs/) you can run the documentation locally without using `docker`:

```console
poetry install
poetry run mkdocs serve
```

### Running locally

```console
docker compose -f local.yml up --build
```

Note: this uses the `.envs/local` file provided in the repo. This _must not_ be used in production, it is simply for local development and to ease demonstrating what is required for `.envs/production`, which _must_ be generated separately for deploying via `production.yml`.

It will take some time to download a set of `docker` images required to run locally, after which it should attempt to start the server in the `django` container. If successful, the console should print logs resembling

```console
lwmdb_local_django    | WARNING: This is a development server. Do not use it in a production
deployment. Use a production WSGI server instead.
lwmdb_local_django    |  * Running on all addresses (0.0.0.0)
lwmdb_local_django    |  * Running on http://127.0.0.1:8000
lwmdb_local_django    |  * Running on http://172.20.0.4:8000
lwmdb_local_django    | Press CTRL+C to quit
lwmdb_local_django    |  * Restarting with stat
lwmdb_local_django    | Performing system checks...
lwmdb_local_django    |
lwmdb_local_django    | System check identified no issues (0 silenced).
lwmdb_local_django    |
lwmdb_local_django    | Django version 4.2.1, using settings 'lwmdb.settings'
lwmdb_local_django    | Development server is running at http://0.0.0.0:8000/
lwmdb_local_django    | Using the Werkzeug debugger (http://werkzeug.pocoo.org/)
lwmdb_local_django    | Quit the server with CONTROL-C.
lwmdb_local_django    |  * Debugger is active!
lwmdb_local_django    |  * Debugger PIN: 139-826-693
```

Indicating it's up and running. You should then be able to go to `http://127.0.0.1:8000` in your local browser and see a start page.

To stop the app call the `down` command:

```console
docker compose -f local.yml down
```

### Importing data

If a previous version of the database is available as either `json` fixtures or raw `sql` via a `pg_dump` (or similar) command.

#### `json` import

`json` `fixtures` need to be placed in a `fixtures` folder in your local checkout:

```console
cd lwmdb
mkdir fixtures
cp DataProvider-1.json  Ingest-1.json Item-1.json Newspaper-1.json Digitisation-1.json Issue-1.json Item-2.json fixtures/
```

The files can then be imported via

```console
docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Newspaper-1.json
docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Issue-1.json
docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Item-2.json
...
```

> :warning: Note the import order is important, specifically: `Newspaper`, `Issue` and any other data `json` files _prior_ to `Item` `json`.

#### Importing a `postgres` database

Importing from `json` can be very slow. If provided a `postgres` data file, it is possible to import that directly. First copy the database file(s) to a `backups` folder on the `postgres` instance (assuming you've run the `build` command)

```console
docker cp backups $(docker compose -f local.yml ps -q postgres):/backups
```

Next make sure the app is shut down, then start up with _only the `postgres`_ container running:

```console
docker compose -f local.yml down
docker compose -f local.yml up postgres
```

Then run the `restore` command with the filename of the backup. By default backup filenames indicates when the backup was made and are compressed (using [`gzip`](https://en.wikipedia.org/wiki/Gzip) compression in the example below `backup_2023_04_03T07_22_10.sql.gz` ):

> :warning: There is a chance the default `docker` size allocated is not big enough for a full version of the dataset (especially if running on a desktop). If so, you may need to increase the allocated disk space. For example, see [`Docker Mac FAQs`](https://docs.docker.com/desktop/faqs/macfaqs/#where-does-docker-desktop-store-linux-containers-and-images) for instructions to increase available disk space.

```console
docker compose -f local.yml exec postgres restore backup_2023_04_03T07_22_10.sql.gz
```

> :warning: If the version of the database you are loading is _not_ compatible with the current version of the python package, this can cause significant errors.

## Querying the database

### Jupyter Notebook

In order to run the Django framework inside a notebook, open another terminal window once you have it running via `docker` as described above and run

```console
docker compose -f local.yml exec django /app/manage.py shell_plus --notebook
```

This should launch a normal Jupyter Notebook in your browser window where you can create any notebooks and access the database in different ways.

**Important:** Before importing any models and working with the database data, you will want to run the `import django_initialiser` in a cell, which will set up all the dependencies needed.

_Note:_ For some users we provide two `jupyter` `notebooks`:

- `getting-started.ipynb`
- `explore-newspapers.ipynb`

Both will give some overview of how one can access the database’s information and what one can do with it. They only scratch the surface of what is possible, of course, but will be a good entry point for someone who wants to orient themselves toward the database and Django database querying.

## Upgrade development version

In order to upgrade the current development version that you have, make sure that you have synchronised the repository to your local drive:

**Step 1**: `git pull`

**Step 2**: `docker compose -f local.yml up --build`

## Run on a server

To run in production, an `.envs/production` `ENV` file must be created. This must befilled in with _new passwords for each key_ rather than a copy of `.envs/local`. The same keys set in `.envs/local` are needed, as well as the follwing two:

- `TRAEFIK_EMAIL="email.register.for.traefik.account@test.com"`
- `HOST_URL="host.for.lwmdb.deploy.org"`

A domain name (in this example `"host.for.lwmdb.deploy.org`) must be registered for `https` (encripyted) usage, and a `TLS` certificate is needed. See [`traefik` docs](https://doc.traefik.io/traefik/https/acme/) for details.

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="http://www.westerling.nu"><img src="https://avatars.githubusercontent.com/u/7298727?v=4?s=100" width="100px;" alt="Kalle Westerling"/><br /><sub><b>Kalle Westerling</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=kallewesterling" title="Code">💻</a> <a href="#ideas-kallewesterling" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/Living-with-machines/lwmdb/commits?author=kallewesterling" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/griff-rees"><img src="https://avatars.githubusercontent.com/u/60181741?v=4?s=100" width="100px;" alt="griff-rees"/><br /><sub><b>griff-rees</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=griff-rees" title="Code">💻</a> <a href="#ideas-griff-rees" title="Ideas, Planning, & Feedback">🤔</a> <a href="#mentoring-griff-rees" title="Mentoring">🧑‍🏫</a> <a href="#maintenance-griff-rees" title="Maintenance">🚧</a> <a href="https://github.com/Living-with-machines/lwmdb/commits?author=griff-rees" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/AoifeHughes"><img src="https://avatars.githubusercontent.com/u/10923695?v=4?s=100" width="100px;" alt="Aoife Hughes"/><br /><sub><b>Aoife Hughes</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=AoifeHughes" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/thobson88"><img src="https://avatars.githubusercontent.com/u/26117394?v=4?s=100" width="100px;" alt="Tim Hobson"/><br /><sub><b>Tim Hobson</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=thobson88" title="Code">💻</a> <a href="#ideas-thobson88" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://npedrazzini.github.io"><img src="https://avatars.githubusercontent.com/u/35242366?v=4?s=100" width="100px;" alt="Nilo Pedrazzini"/><br /><sub><b>Nilo Pedrazzini</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=npedrazzini" title="Code">💻</a> <a href="#ideas-npedrazzini" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://christinalast.com"><img src="https://avatars.githubusercontent.com/u/36204574?v=4?s=100" width="100px;" alt="Christina Last"/><br /><sub><b>Christina Last</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=ChristinaLast" title="Code">💻</a> <a href="#ideas-ChristinaLast" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/claireaustin01"><img src="https://avatars.githubusercontent.com/u/45455829?v=4?s=100" width="100px;" alt="claireaustin01"/><br /><sub><b>claireaustin01</b></sub></a><br /><a href="#ideas-claireaustin01" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="http://openobjects.org.uk"><img src="https://avatars.githubusercontent.com/u/380763?v=4?s=100" width="100px;" alt="Mia"/><br /><sub><b>Mia</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=mialondon" title="Code">💻</a> <a href="#ideas-mialondon" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/Living-with-machines/lwmdb/commits?author=mialondon" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/andrewphilipsmith"><img src="https://avatars.githubusercontent.com/u/5346065?v=4?s=100" width="100px;" alt="Andy Smith"/><br /><sub><b>Andy Smith</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=andrewphilipsmith" title="Code">💻</a> <a href="#ideas-andrewphilipsmith" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://www.turing.ac.uk/people/researchers/katherine-mcdonough"><img src="https://avatars.githubusercontent.com/u/20363927?v=4?s=100" width="100px;" alt="Katie McDonough"/><br /><sub><b>Katie McDonough</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=kmcdono2" title="Code">💻</a> <a href="#ideas-kmcdono2" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/mcollardanuy"><img src="https://avatars.githubusercontent.com/u/46483603?v=4?s=100" width="100px;" alt="Mariona"/><br /><sub><b>Mariona</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=mcollardanuy" title="Code">💻</a> <a href="#ideas-mcollardanuy" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/kasparvonbeelen"><img src="https://avatars.githubusercontent.com/u/11618160?v=4?s=100" width="100px;" alt="Kaspar Beelen"/><br /><sub><b>Kaspar Beelen</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=kasparvonbeelen" title="Code">💻</a> <a href="#ideas-kasparvonbeelen" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/DavidBeavan"><img src="https://avatars.githubusercontent.com/u/6524799?v=4?s=100" width="100px;" alt="David Beavan"/><br /><sub><b>David Beavan</b></sub></a><br /><a href="https://github.com/Living-with-machines/lwmdb/commits?author=DavidBeavan" title="Code">💻</a> <a href="#ideas-DavidBeavan" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
