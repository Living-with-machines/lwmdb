**`lib_metadata_db`**
=========
A pip package containing database access functionality which can be imported in any project requiring this access.

Database
===========
Clone the '.env.sample' and name it '.env'. You will then need to insert your own credentials into it.

Dependencies
============
This project uses ``poetry`` as a package manager. you can read more about it at [`poetry-docs`](<https://python-poetry.org/docs/>). We recommend setting up ``poetry`` with [``pyenv``](https://blog.jayway.com/2019/12/28/pyenv-poetry-saviours-in-the-python-chaos/) to manage python versions between local projects.

Apache
-----------------------------

For Apache, is included the xcode command line tools

``$ xcode-select --install``

followed by:

``$ brew install httpd``

postgresql
-----------------------------

On mac:

``$ brew install postgresql``

followed by:

``$ brew services restart postgresql``

poetry
-----------------------------

To create models for an app:
-----------------------------

``python lib_metadata_db/manage.py makemigrations APP_NAME``

If ``APP_NAME`` not specified, migrations for all ``INSTALLED_APPS`` would be created

Creating/Updating tables in the database:
-----------------------------------------

Make sure to specify the ``APP_NAME`` when migrating the changes to ensure that the migrations from other apps in the project are not pushed to the database.

``python lib_metadata_db/manage.py migrate APP_NAME --database=DATABASE_NAME``


To check the tables have been created enter ``psql`` using the correct username and database name:

``psql -U newspapers -d newspapers_db``

To see the tables:
``\dt``

Importing Data
==============
In order to import new data into a table in the database:

``python lib_metadata_db/manage.py import_TABLE_NAME PATH_TO_FILE``
