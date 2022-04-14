**`lib_metadata_db`**
=========
A pip package containing database access functionality which can be imported in any project requiring this access.

Dependencies
============
This project uses `poetry` as a package manager. you can read more about it at [`poetry-docs`](<https://python-poetry.org/docs/>). We recommend setting up `poetry` using `pyenv` to install specific versions of `python`, see [here](https://blog.jayway.com/2019/12/28/pyenv-poetry-saviours-in-the-python-chaos/) to manage python versions between local projects.

`Apache` install
-----------------------------

We recommend using `homebrew` to install the following:

```shell
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
For Apache, is included the `xcode` command line tools

```shell
$ xcode-select --install
```
followed by:

```shell
$ brew install httpd
```

``postgresql`` install
----------------

On mac:

```shell
$ brew install postgresql
```

followed by:

```shell
$ brew services start postgresql
```

``poetry`` installation for managing dependencies
-----------------------------

To install `python` packages via `poetry` run:

```shell
$ poetry install
````

and to enter the virtual environment

```shell
$ poetry shell
````
Clone the '`.env.sample`' and name it '`.env`'. You will then need to insert your own credentials into it.

Database setup
===========

### Create a `User` in `postgresql`

These instructions are adapted from [this source](https://www.sqlshack.com/setting-up-a-postgresql-database-on-mac/):
1. Log in to postgres service to execute PGSQL commands:

```shell
$ psql postgres
```

2. Create a `user` with a `password` and a `database` in `postgresql`

```PGSQL
CREATE ROLE newspapers WITH LOGIN PASSWORD 'newspapers';
CREATE DATABASE newspapers_db;
GRANT ALL PRIVILEGES ON DATABASE newspapers_db TO newspapers;
```
3. Quit the current session:

```PGSQL
\q
```
4. Reconnect with the new user’s credentials:

```shell
$ psql -d newspapers_db -U newspapers
```

4. To see the tables:

```PGSQL
\dt
```
To create models for an app:
-----------------------------
Make sure to specify the `APP_NAME` when making a migration to ensure that other changes inherited in your schema are not pushed to the database. The best way to do this is to `makemigrations` for each `APP_NAME` individually.

```shell
python lib_metadata_db/manage.py makemigrations newspapers
```
If `APP_NAME` not specified, migrations for all `INSTALLED_APPS` would be created

```shell
python lib_metadata_db/manage.py makemigrations
```

Creating/Updating tables in the database:
-----------------------------------------

Make sure to specify the `APP_NAME` when migrating the changes to ensure that the migrations from other apps in the project are not pushed to the database.

```shell
python lib_metadata_db/manage.py migrate APP_NAME --database=DATABASE_NAME
```

Importing Data
==============
In order to import new data into a table in the database:

```shell
python lib_metadata_db/manage.py import_TABLE_NAME PATH_TO_FILE
```
