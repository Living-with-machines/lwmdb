# Deploy

There are two main options for deploying this data. Both require `docker` to manage build, testing and interoperability, and at the time of this writing *at least* 30 GB of free harddrive space, preferable two or three times that for flexibility.

## Local Deploy:

Local deploys are well suited for

- Individual research
- Testing new features
- Contributing to bug fixes or documentation

Assuming a personal computer, `docker` [Desktop](https://www.docker.com/products/docker-desktop/) is one of the easier options and works for `Linux` distributions, `Windows` and `macOS`.

### Clone repository to local drive

Run the following command on your command line:

```console
git clone git@github.com:Living-with-machines/lib_metadata_db.git
cd lib_metadata_db
```

The subsequent sections assume commands are run from within the `lib_metadata_db` folder.

### Local Build

=== "user"

    ```console
    docker compose -f local.yml up --build
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml up --build
    ```

This uses the `.envs/local` file provided in the repo. This *must not* be used in production, it is simply for local development and to ease demonstrating what is required for `.envs/production`, which *must* be generated separately for deploying via `production.yml`.

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
metadata_local_django    | Django version 4.2, using settings 'metadata.settings'
metadata_local_django    | Development server is running at http://0.0.0.0:8000/
metadata_local_django    | Using the Werkzeug debugger (http://werkzeug.pocoo.org/)
metadata_local_django    | Quit the server with CONTROL-C.
metadata_local_django    |  * Debugger is active!
metadata_local_django    |  * Debugger PIN: 139-826-693
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

## Production Deploy

A local production deploy should be available without aditional modification. Deploying for exteral users is a more involved process and will require registering a domain name.

To run in production, a `.envs/production` `ENV` file is required. This is not provided to help ensure encryption keys are generated uniquely by users. These are specifically for 

- `SECRET_KEY`
- `POSTGRES_PASSWORD`

as well as the follwing two:

- `TRAEFIK_EMAIL="email.register.for.traefik.account@test.com"`
- `HOST_URL="host.for.lwmdb.deploy.org"`

## `traefik` Config

A domain name (in this example `"host.for.lwmdb.deploy.org`) must be registered for `https` (encripyted) usage, and a `TLS` certificate is needed. See [`traefik` docs](https://doc.traefik.io/traefik/https/acme/) for details.

## Generating password config

There are numerous methods for generating keys. `python` provides an option via the `secrets` module:

```python
import secrets

print(secrets.token_urlsafe())"
```

For convenience and minimising risks like screencapture, this can be run and piped to your local clipboard. Examples for different operating systems:

=== "linux"

    ```console
    python -c "import secrets; print(secrets.token_urlsafe())" | xclip
    ```

=== "macOS"

    ```console
    python -c "import secrets; print(secrets.token_urlsafe())" | pbcopy
    ```

=== "windows"

    ```console
    python -c "import secrets; print(secrets.token_urlsafe())" | /dev/clipboard
    ```

If arranging this via a deploy service like `azure`, it is also possible to add keys/config within the local environment or via an `export` command (assuming a `bash` or `zsh` shell).
