**`lib_metadata_db`**
=========
A pip package containing database access functionality which can be imported in any project requiring this access.

Dependencies
============
This project uses `poetry` as a package manager. You can read more about it at [`poetry-docs`](<https://python-poetry.org/docs/>). We recommend setting up `poetry` using `pyenv` to install specific versions of `python`, see [here](https://blog.jayway.com/2019/12/28/pyenv-poetry-saviours-in-the-python-chaos/) to manage python versions between local projects.

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

``postgis`` dependency installation
----------------

Instructions are taken from [this webpage](https://morphocode.com/how-to-install-postgis-on-mac-os-x/)

In the terminal run:
```shell
$ brew install postgis
```

then
```shell
$ brew services start postgresql
```

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
ALTER ROLE newspapers SUPERUSER;
```
3. Quit the current session:

```PGSQL
\q
```
4. Reconnect with the new user’s credentials:

```shell
$ psql -d newspapers_db -U newspapers
```

5. To check your user permissions use:

```PGSQL
\l
```

You should see something like this:
```
List of databases
Name      |  Owner   | Encoding |   Collate   |    Ctype    |    Access privileges    
---------------+----------+----------+-------------+-------------+-------------------------
postgres      | <your-user>    | UTF8     | en_GB.UTF-8 | en_GB.UTF-8 |
newspapers_db | postgres       | UTF8     | en_GB.UTF-8 | en_GB.UTF-8 | =Tc/postgres           +
|             |                |          |             | postgres=CTc/postgres  +
|             |                |          |             | newspapers=CTc/postgres
```

If so, great! use `\q` to quit the session and continue.


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

Make sure to specify the `APP_NAME` (in our initial table `APP_NAME=newspapers`) and the database (in our initial instance `DATABASE_NAME=newspapers_db`) when migrating the changes to ensure that the migrations from other apps in the project are not pushed to the database.

```shell
python lib_metadata_db/manage.py migrate newspapers --database=newspapers_db
```

1. To see the tables login with your newly created `user`:

```shell
$ psql -d newspapers_db -U newspapers
```

2. and view the tables you created:

```PGSQL
\dt
```

Migrating models across all DATABASES
-----------------------------------------

1. run the following from the command line:

```shell
$ psql newspapers_db -c "GRANT ALL ON ALL TABLES IN SCHEMA public to newspapers;"
$ psql newspapers_db -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public to newspapers;"
$ psql newspapers_db -c "GRANT ALL ON ALL FUNCTIONS IN SCHEMA public to newspapers;"
```
2. Then go ahead and migrate your new models in whichever database, such as

```shell
$ python lib_metadata_db/manage.py makemigrations press_directories
```

View schema and tables
==============
Download your favourite Database manager tool! The following example uses [`DBeaver`](https://dbeaver.io/download/)

```shell
$ brew install --cask dbeaver-community
```

Open `DBeaver` and add the credentials to connect your local instance of the database using the credentials in your ``.env`` file. You should then be able to navigate within ``newspapers_db`` to "Schemas" -> "public" -> "tables" to see the migrated models as tables.


Importing Data
==============
In order to import new data into a table in the database:

```shell
$ python lib_metadata_db/manage.py import_TABLE_NAME PATH_TO_FILE
```

Schema Diagram
==============
View a diagram of the databases [here](https://dbdiagram.io/d/627bd08a7f945876b6fca7d0).
