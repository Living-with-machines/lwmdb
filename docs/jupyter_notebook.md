## Querying the database

### Jupyter Notebook

In order to run the Django framework inside a notebook, open another terminal window once you have it running via `docker` as described above and run


=== "user"

    ```console
    docker compose -f local.yml exec django /app/manage.py shell_plus --notebook
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml exec django /app/manage.py shell_plus --notebook
    ```

This should launch a normal Jupyter Notebook in your browser window where you can create any notebooks and access the database in different ways.

!!! Important

    Before importing any models and working with the database data, you will want to run the `import django_initialiser` in a cell, which will set up all the dependencies needed.

The package comes with a `getting-started.ipynb` notebook and a `explore-newspapers.ipynb` notebook, which both will give some overview of how one can access the database’s information and what one can do with it. They only scratch the surface of what is possible, of course, but will be a good entry point for someone who wants to orient themselves toward the database and the Django syntax for querying.
