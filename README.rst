**`lib_metadata_db`**
=========
A pip package containing database access functionality which can be imported in any project requiring this access.

Dependencies
============
This project uses ``poetry`` as a package manager. you can read more about it at [`poetry-docs`](<https://python-poetry.org/docs/>). We recommend setting up ``poetry`` with [``pyenv``](https://blog.jayway.com/2019/12/28/pyenv-poetry-saviours-in-the-python-chaos/) to manage python versions between local projects.

``Apache`` install
-----------------------------

We recommend using homebrew to install the following:
```shell
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
For Apache, is included the xcode command line tools

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
$ brew services restart postgresql
````

``poetry`` installation for managing dependencies
-----------------------------

To install python packages via poetry run:

```shell
$ poetry install
````

and to enter the virtual environment

```shell
$ poetry shell
````
Clone the '``.env.sample``' and name it '``.env``'. You will then need to insert your own credentials into it.

Database setup
===========

### Create a `User` in `postgresql`

These instructions are adapted from [this source](https://www.sqlshack.com/setting-up-a-postgresql-database-on-mac/):
1. Log in to postgres service to execute PGSQL commands:

```shell
$ psql postgres
```

2. Create a user with a password:

```PGSQL
CREATE ROLE newspapers WITH LOGIN PASSWORD newspapers;
ALTER ROLE newspapers CREATEDB;
```
3. Quit the current session:

```PGSQL
\q
```
4. Reconnect with the new user’s credentials:

```shell
$ psql postgres -U newspapers
```
### Creating a `database` in `postgresql`

1. After reconnecting to ``psql`` with the user credentials you have created, in the above instruction:

```PGSQL
CREATE DATABASE newspapers_db;
GRANT ALL PRIVILEGES ON DATABASE newspapers_db TO newspapers;
```
2. Quit the current session:

```PGSQL
\q
```

3. To check the tables have been created enter ``psql`` using the correct username and database name:

```shell
$ psql -U newspapers -d newspapers_db
```

4. To see the tables:

```PGSQL
\dt
```
### Installing PGAdmin to navigate Postgres Database server

Navigate to https://www.pgadmin.org/ and download the DMG and install it. Once installed, provide the credentials as follows.
```
    host – “localhost”
    user – “newuser”
    password – “password”
    maintenance database – “postgres”
```
Once you log in, you can see all the various functions that can be used within PGAdmin.


To create models for an app:
-----------------------------

```shell
python lib_metadata_db/manage.py makemigrations
```
If ``APP_NAME`` not specified, migrations for all ``INSTALLED_APPS`` would be created

```shell
python lib_metadata_db/manage.py makemigrations APP_NAME
```
Creating/Updating tables in the database:
-----------------------------------------

Make sure to specify the ``APP_NAME`` when migrating the changes to ensure that the migrations from other apps in the project are not pushed to the database.

```shell
python lib_metadata_db/manage.py migrate APP_NAME --database=DATABASE_NAME
```



Importing Data
==============
In order to import new data into a table in the database:

```shell
python lib_metadata_db/manage.py import_TABLE_NAME PATH_TO_FILE
```
