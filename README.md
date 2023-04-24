# Metadata database code

A package containing database access to the Living with Machines newspaper collection’s metadata.

## Installation

### Install Docker

It is possible to run this code without Docker, but at present we are only maintaining it via Docker Containers so we *highly* recommend installing Docker to run and/or test this code locally. Instructions are available for most operating systems here: https://docs.docker.com/desktop/

### Clone repository to local drive

Run the following command on your command line:

```
$ git clone git@github.com:Living-with-machines/lib_metadata_db.git
```

Follow by:

```
$ cd lib_metadata_db
```

### Running locally

```console
$ docker compose -f local.yml up --env-file=.envs/local --build
```

Note: this uses the `.envs/local` file provided in the repo. This *must not* be used in production, it is simply for local development and to ease demonstrating what is required for `.envs/production`, which *must* be generated separately for deploying via `production.yml`.

It will take some time to download a set of `docker` images required to run locally, after which it should attempt to start the server in the `django` container. If successful, the console should print logs resembling

```console
metadata_local_django    | WARNING: This is a development server. Do not use it in a production
deployment. Use a production WSGI server instead.
metadata_local_django    |  * Running on all addresses (0.0.0.0)
metadata_local_django    |  * Running on http://127.0.0.1:8000
metadata_local_django    |  * Running on http://172.20.0.4:8000
metadata_local_django    | Press CTRL+C to quit
metadata_local_django    |  * Restarting with stat
metadata_local_django    | Performing system checks...
metadata_local_django    |
metadata_local_django    | System check identified no issues (0 silenced).
metadata_local_django    |
metadata_local_django    | Django version 4.1.7, using settings 'metadata.settings'
metadata_local_django    | Development server is running at http://0.0.0.0:8000/
metadata_local_django    | Using the Werkzeug debugger (http://werkzeug.pocoo.org/)
metadata_local_django    | Quit the server with CONTROL-C.
metadata_local_django    |  * Debugger is active!
metadata_local_django    |  * Debugger PIN: 139-826-693
```

Indicating it's up and running. You should then be able to go to `http://127.0.0.1:8000` in your local browser and see a start page.

To stop the app call the `down` command:

```console
$ docker compose -f local.yml --env-file=.envs/local down
```

### Importing data

If a previous version of the database is available as either `json` fixtures or raw `sql` via a `pg_dump` (or similar) command.

#### `json` import

`json` `fixtures` need to be placed in a `fixtures` folder in your local checkout:

```console
$ cd lib_metadata_db
$ mkdir fixtures
$ cp DataProvider-1.json  Ingest-1.json Item-1.json Newspaper-1.json Digitisation-1.json Issue-1.json Item-2.json fixtures/
```

The files can then be imported via

```console
$ docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Newspaper-1.json
$ docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Issue-1.json
$ docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Item-2.json
...
```

> :warning: Note the import order is important, specifically: `Newspaper`, `Issue` and any other data `json` files *prior* to `Item` `json`.

#### Importing a `postgres` database

Importing from `json` can be very slow. If provided a `postgres` data file, it is possible to import that directly. First copy the database file(s) to a `backups` folder on the `postgres` instance (assuming you've run the `build` command)

```console
docker compose -f local.yml cp backups/* $(docker compose -f local.yml ps -q postgres):/backups/
```

Next make sure the app is shut down, then start up with *only the `postgres`* container running:

```console
docker compose -f local.yml down
docker compose -f local.yml up postgres
```

Then run the `restore` command with the filename of the backup. By default backup filenames indicates when the backup was made and are compressed (using [`gzip`](https://en.wikipedia.org/wiki/Gzip) compression in the example below `backup_2023_04_03T07_22_10.sql.gz` ) :

> :warning: There is a chance the default `docker` size allocated is not big enough for a full version of the dataset (especially if running on a desktop). If so, you may need to increase the allocated disk space. For example, see [`Docker Mac FAQs`](https://docs.docker.com/desktop/faqs/macfaqs/#where-does-docker-desktop-store-linux-containers-and-images) for instructions to increase available disk space.

```console
docker compose -f local.yml exec postgres restore backup_2023_04_03T07_22_10.sql.gz
```

> :warning: If the version of the database you are loading is *not* compatible with the current version of the python package, this can cause significant errors.

## Querying the database

### Jupyter Notebook

In order to run the Django framework inside a notebook, open another terminal window once you have it running via `docker` as described above and run

```console
$ docker compose -f local.yml exec django /app/manage.py shell_plus --notebook
```

This should launch a normal Jupyter Notebook in your browser window where you can create any notebooks and access the database in different ways.

**Important:** Before importing any models and working with the database data, you will want to run the `import django_initialiser` in a cell, which will set up all the dependencies needed.

*Note:* The package comes with a `getting-started.ipynb` notebook and a `explore-newspapers.ipynb` notebook, which both will give some overview of how one can access the database’s information and what one can do with it. They only scratch the surface of what is possible, of course, but will be a good entry point for someone who wants to orient themselves toward the database and the Django syntax for querying.

## Upgrade development version

In order to upgrade the current development version that you have, make sure that you have synchronised the repository to your local drive:

**Step 1**: `$ git pull`

**Step 2**: `$ docker compose -f local.yml --env-file=.envs/local up --build`

## Accessing full-text using `extract_fulltext` method

We are developing a fulltext table for all articles across our available newspapers. Meanwhile, @thobson88 has developed an `.extract_fulltext()` method that can be used on any `Item` objects. Here is an example:

```py
from newspapers.models import Newspaper
from newspapers.models import Item
from pathlib import Path

# Set the local download path:
Item.DOWNLOAD_DIR = Path.home() / "temp/fulltext"

# Set the SAS token:
%env FULLTEXT_SAS_TOKEN="?an=SSH&token=true"

item = Newspaper.objects.get(publication_code="0003040").issues.first().items.first()
item.extract_fulltext()
```

If you need help setting up a SAS token, see [instructions here](https://github.com/Living-with-machines/fulltext#sas-token-creation).

_Please note, access via Blobfuse is planned but not yet implemented._

## Running on a server

To run in production, a `.envs/production` `ENV` file is required. This is not provided to help encryption keys are generated locally and uniquely. The keys set in `.envs/local` are all needed, as well as the follwing two:

- TRAEFIK_EMAIL="email.register.for.traefik.account@test.com"
- HOST_URL="host.for.lwmdb.deploy.org"

A domain name (in this example `"host.for.lwmdb.deploy.org`) must be registered for `https` (encripyted) usage, and a `TLS` certificate is needed. See [`traefik` docs](https://doc.traefik.io/traefik/https/acme/) for details.

## Troubleshooting: Common issues

### `Error: ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured.`

**Problem:** I have received an error that looks like this:

> ImproperlyConfigured&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Traceback (most recent call last)
> ...
> ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured. You must either define the environment variable DJANGO_SETTINGS_MODULE or call settings.configure() before accessing settings.

**Explanation:** You have likely attempted to import any of the models (`Newspaper`, `Item`, `Entry`, etc.) and forgotten about the `import django_initialiser` statement that is required to set up Django in a Jupyter Notebook.

**Solution:** You must run `import django_initialiser` before you attempt to import any models from the Django package.

**If it does not work:** Are you running the notebook in the same folder as the `manage.py` script? Otherwise, try to move the notebook to that folder.

### `NameError: name 'Newspaper' is not defined`

**Problem:** I have received an error that looks like this:

> ---------------------------------------------------------------------------
> NameError&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Traceback (most recent call last)
> ...
> NameError: name 'Newspaper' is not defined

**Explanation:** You have likely forgotten to import the correct model before you tried to run a query on one of the newspapers (or whichever model you’re trying to access).

**Solution:** Run `from newspapers.models import Newspaper` or follow the same pattern for whichever model you want to import. (See the database schema if you are unsure which model you want to access.)

**If it does not work:** Are you running the notebook in the same folder as the `manage.py` script? Otherwise, try to move the notebook to that folder.
