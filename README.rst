**`lib_metadata_db`**
=========
A pip package containing database access functionality which can be imported in any project requiring this access.

Database
===========
Clone the '.env.sample' and name it '.env'. You will then need to insert your own credentials into it.

Dependencies
============
This project uses poetry, you can read more about it at [`poetry-docs`](<https://python-poetry.org/docs/>).

To create models for an app:
-----------------------------

``python lib_metadata_db/manage.py makemigrations APP_NAME``

If ``APP_NAME`` not specified, migrations for all ``INSTALLED_APPS`` would be created

Creating/Updating tables in the database:
-----------------------------------------

Make sure to specify the ``APP_NAME`` when migrating the changes to ensure that the migrations from other apps in the project are not pushed to the database.

``python lib_metadata_db/manage.py migrate APP_NAME --database=DATABASE_NAME``

Importing Data
==============
In order to import new data into a table in the database:

``python lib_metadata_db/manage.py import_TABLE_NAME PATH_TO_FILE``
