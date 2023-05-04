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

```
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

## Local Encryption (`https`)

!!! warning 
    
    This section of documentation is no longer usable and will be replaced due to errors in the official documentation (see [#2840](https://github.com/cookiecutter/cookiecutter-django/issues/2840) for example). Another solution will be added in the future.

Note the example url's provided above are primarily `http` via ports `8000` (like `http://127.0.0.1:8000`). Web security---even when running work locally---has become a crucial element of even local development, and to work towards a production deploy local encryption is a very helpful process.

[`django-cookie-cutter`](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally-docker.html#developing-locally-with-https) suggests options for using [Fillipo Valsorda's](https://filippo.io/) [`mkcert`](https://github.com/FiloSottile/mkcert).

To install `mkcert` follow the install [docs](https://github.com/FiloSottile/mkcert#installation)  and t. Once installed, follow the instructions to generate a local host certificate:

=== "user"

```console
mkcert -install
Created a new local CA 💥
Sudo password:
The local CA is now installed in the system trust store! ⚡️
The local CA is now installed in the Firefox trust store (requires browser restart)! 🦊
```

Once installed, create a `certs` local directory in the same folder as the `local.yml` file, and enter it to generate a local certificate files

```console
mkdir certs
cd certs
mkcert lwmdb-test.local localhost 127.0.0.1 ::1

Created a new certificate valid for the following names 📜
 - "lwmdb-test.local"
 - "localhost"
 - "127.0.0.1"
 - "::1"

The certificate is at "./lwmdb-test.local+3.pem" and the key at "./lwmdb-test.local+3-key.pem" ✅

It will expire on 25 July 2025 🗓
```

For the generated keys to work with `nginx-proxy`, they need to be renamed as follows:

```console
mv lwmdb-test.local+3.pem lwmdb-test.local.crt
mv lwmdb-test.local+3-key.pem lwmdb-test.local.key
```

Once generated and stored, rebuild:

=== "user"

    ```console
    docker compose -f local.yml up --build
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml up --build
    ```

!!! note 

    Default configuration of certificates expire every 3 months
    (hence the `+3` file name) after generation. Follow the
    `mkcert` instructions as necessary to replace expired `certs`
    files.

Once up, you can test the configuration with:

```console
curl -H "Host: lwmdb-test.local" localhost
```

It may have configuration issues leading to a response like

```html
<html>
<head><title>301 Moved Permanently</title></head>
<body>
<center><h1>301 Moved Permanently</h1></center>
<hr><center>nginx/1.23.4</center>
</body>
</html>
```

This is a known issue currently being addressed.

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
