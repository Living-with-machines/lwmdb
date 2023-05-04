# Troubleshooting: Common issues

## `Error: ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured.`

**Problem:** I have received an error that looks like this:

> ImproperlyConfigured&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Traceback (most recent call last)
> ...
> ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured. You must either define the environment variable DJANGO_SETTINGS_MODULE or call settings.configure() before accessing settings.

**Explanation:** You have likely attempted to import any of the models (`Newspaper`, `Item`, `Entry`, etc.) and forgotten about the `import django_initialiser` statement that is required to set up Django in a Jupyter Notebook.

**Solution:** You must run `import django_initialiser` before you attempt to import any models from the Django package.

**If it does not work:** Are you running the notebook in the same folder as the `manage.py` script? Otherwise, try to move the notebook to that folder.

## `NameError: name 'Newspaper' is not defined`

**Problem:** I have received an error that looks like this:

> ---------------------------------------------------------------------------
> NameError&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Traceback (most recent call last)
> ...
> NameError: name 'Newspaper' is not defined

**Explanation:** You have likely forgotten to import the correct model before you tried to run a query on one of the newspapers (or whichever model you’re trying to access).

**Solution:** Run `from newspapers.models import Newspaper` or follow the same pattern for whichever model you want to import. (See the database schema if you are unsure which model you want to access.)

**If it does not work:** Are you running the notebook in the same folder as the `manage.py` script? Otherwise, try to move the notebook to that folder.
