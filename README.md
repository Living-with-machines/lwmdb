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
$ docker compose -f local.yml up --build
```

It will take some time to download a set of `docker` images required to run locally, after which it should attempt to start the server in the `django` container. If successful, the console should print

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

### Put the database into place

Now you need to access the **correct** and **most up-to-date** version of the database and place files in the `fixtures` folder. Currently these need to be requested. Feel free to report an [issue](https://github.com/Living-with-machines/lib_metadata_db/issues) indicating you need fixtures and we will help provide that if permission allows.

Assuming data is available, you should be able to import the data provided by placing those files in a `fixtures` folder in your local checkout:

```console
$ cd lib_metadata_db
$ mkdir fixtures
$ cp DataProvider-1.json  Ingest-1.json Item-1.json Newspaper-1.json Digitisation-1.json Issue-1.json Item-2.json fixtures/
```

The files can then be processed by loading each via

```console
$ docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Newspaper-1.json
$ docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Item-2.json 
...
```

Once all of these are loaded, you should be able to interact with the database.

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

In order to upgrade the current development version that you have, make sure that you have synchronised the repository to your local drive, and that you have dropped the correct and most up-to-date `db.sqlite3` file into the same folder as the `manage.py` file. (See above, under ”Put the database into place“, for further explanation.)

**Step 1**: `$ git pull`

**Step 2**: `$ docker compose -f local.yml up --build`

## Accessing full-text using `extract_fulltext` method

We are developing a fulltext table for all articles across our available newspapers. Meanwhile, @thobson88 has developed an `.extract_fulltext()` method that can be used on any `Item` objects. Here is an example:

```py
from newspapers.models import Newspaper
from newspapers.models import Item
from pathlib import Path

# Set the local download path:
Item.DOWNLOAD_DIR = Path.home() / "temp/fulltext"

# Set the SAS token:
%env FULLTEXT_SAS_TOKEN="?sv=2021-06-08&ss=bfqt&srt=sco&sp=rtf&se=2022-10-04T17:49:53Z&st=2022-10-04T09:49:53Z&sip=82.16.244.16&spr=https&sig=Kp6QEtqWw5NlJZx4r0eddSxfjqXzXEeY0pwoii%2Fz86E%3D"

item = Newspaper.objects.get(publication_code="0003040").issues.first().items.first()
item.extract_fulltext()
```

If you need help setting up a SAS token, see [instructions here](https://github.com/Living-with-machines/fulltext#sas-token-creation).

_Please note, access via Blobfuse is planned but not yet implemented._

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
