
# Installation

## Install Docker

It is possible to run this code without Docker, but at present we are only maintaining it via Docker Containers so we *highly* recommend installing Docker to run and/or test this code locally. Instructions are available for most operating systems here: https://docs.docker.com/desktop/

## Clone repository to local drive

Run the following on a command line interface:

```console
git clone git@github.com:Living-with-machines/lwmdb.git
cd lwmdb
```

## Running locally

=== "user"

    ```console
    docker compose -f local.yml up --build
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml up --build
    ```

!!! note

    This uses the `.envs/local` file provided in the repo. This *must not* be used in production, it is simply for local development and to ease demonstrating what is required for `.envs/production`, which *must* be generated separately for deploying via `production.yml`.

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
lwmdb_local_django    | Django version 4.1.7, using settings 'lwmdb.settings'
lwmdb_local_django    | Development server is running at http://0.0.0.0:8000/
lwmdb_local_django    | Using the Werkzeug debugger (http://werkzeug.pocoo.org/)
lwmdb_local_django    | Quit the server with CONTROL-C.
lwmdb_local_django    |  * Debugger is active!
lwmdb_local_django    |  * Debugger PIN: 139-826-693
```

Indicating it's up and running. You should then be able to go to `http://127.0.0.1:8000` in your local browser and see a start page.

To stop the app call the `down` command:

=== "user"

    ```console
    docker compose -f local.yml down
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml down
    ```

## Importing data

If a previous version of the database is available as either `json` fixtures or raw `sql` via a `pg_dump` (or similar) command.

### `json` import

`json` `fixtures` need to be placed in a `fixtures` folder in your local checkout:

```console
cd lwmdb
mkdir fixtures
cp DataProvider-1.json  Ingest-1.json Item-1.json Newspaper-1.json Digitisation-1.json Issue-1.json Item-2.json fixtures/
```

The files can then be loaded into the `docker` container via

=== "user"

    ```console
    docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Newspaper-1.json
    docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Issue-1.json
    docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Item-2.json
    ...
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Newspaper-1.json
    sudo docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Issue-1.json
    sudo docker compose -f local.yml exec django /app/manage.py loaddata fixtures/Item-2.json
    ...
    ```

!!! warning 

    Note the import order is important, specifically: `Newspaper`, `Issue` and any other data `json` files *prior* to `Item` `json`.

### Importing a `postgres` database

Importing from `json` can be very slow. If provided a `postgres` data file, it is possible to import that directly. First copy the database file(s) to a `backups` folder on the `postgres` instance (assuming you've run the `build` command)

=== "user"

    ```console
    docker cp backups/. $(docker compose -f local.yml ps -q postgres):backups
    ```

=== "sudo"

    ```console
    sudo docker cp backups/. $(sudo docker compose -f local.yml ps -q postgres):backups
    ```

The available backups can be checked with

=== "user"

    ```console
    docker compose -f local.yml exec postgres backups
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml exec postgres backups
    ```

listing files in the desired folder:

```console
sudo docker compose -f local.yml exec postgres ls backups
```

Next make sure the app is shut down, then start up with *only the `postgres`* container running:

=== "user"

    ```console
    docker compose -f local.yml down
    docker compose -f local.yml up postgres
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml down
    sudo docker compose -f local.yml up postgres
    ```

Then run the `restore` command with the filename of the backup. By default backup filenames indicates when the backup was made and are compressed (using [`gzip`](https://en.wikipedia.org/wiki/Gzip) compression in the example below `backup_2023_04_03T07_22_10.sql.gz`):

!!! warning

    There is a chance the default `docker` size allocated is not big enough for a full version of the dataset (especially if running on a desktop). If so, you may need to increase the allocated disk space. For example, see [`Docker Mac FAQs`](https://docs.docker.com/desktop/faqs/macfaqs/#where-does-docker-desktop-store-linux-containers-and-images) for instructions to increase available disk space.

=== "user"

    ```console
    docker compose -f local.yml exec postgres restore backup_2023_04_03T07_22_10.sql.gz
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml exec postgres restore backup_2023_04_03T07_22_10.sql.gz
    ```

!!! warning 

    If the version of the database you are loading is *not* compatible with the current version of the python package, this can cause significant errors

## Upgrade development version

In order to upgrade the current development version that you have, make sure that you have synchronised the repository to your local drive:

=== "user"

    ```console
    git pull
    docker compose -f local.yml up --build
    ```

=== "sudo"

    ```console
    git pull
    sudo docker compose -f local.yml up --build
    ```
