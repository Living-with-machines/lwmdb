# Server Management 

Much of the configuration in this project is derived from [`django-cookiecutter`](https://cookiecutter-django.readthedocs.io), and the information below is derived from their execllent documentation and avoid ambiguities between updates to their configuration and this project.

!!! note

    The viability of this work is very much dependent on the great detail and sophistication of that project, and we are greatful for that work, and the work of the many open source projects we have priviledged to work with and use.

## Managing Data

Managing versions of the datasets included in this project is quite complex, and can take significant time. We advises reading through all the instructions below before running any of the commands provided, and ensuring you have a version consistent with what you have installed locally and run.

### Backing up 

It is helpful to save the database in a state prior to, for example, redepoloying or a refactor. To do this run

=== "user"

    ```console
    docker compose -f local.yml exec postgres backup
    Backing up the 'lwmdb' database...
    SUCCESS: 'lwmdb' database backup 'backup_2023_05_17T12_38_40.sql.gz' has been created and placed in '/backups'.
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml exec postgres backup
    Backing up the 'lwmdb' database...
    SUCCESS: 'lwmdb' database backup 'backup_2023_05_17T12_38_40.sql.gz' has been created and placed in '/backups'.
    ```

Which generates the a backup file (`backup_2023_05_17T12_38_40.sql.gz` in this case) in the `/backups` folder of the `postgres` `docker` container.

This can take some time, but will greate a compressed, complete version of the database, *including login information*, that can then be applied if something breaks or a new deploy on a new computer is needed.

### Listing database backups

Assuming default configurations, all database backup files will be in `/backups/` in a local `postgres` `docker` `container`. To copy that file out, it is helpful to check which backups are available

=== "user"

    ```console
    docker compose -f local.yml exec postgres backups
    These are the backups you have got:
    total 27G
    -rw-r--r-- 1 root root 9.3G May 17 13:14 backup_2023_05_17T12_38_40.sql.gz
    -rw-r--r-- 1 root root 9.3G Apr 18 19:15 backup_2023_04_18T18_41_00.sql.gz
    -rw-r--r-- 1 root root 8.0G Apr  3 07:51 backup_2023_04_03T07_22_10.sql.gz
    ```

=== "sudo"

    ```console
    sudo docker compose -f local.yml exec postgres backups
    These are the backups you have got:
    total 27G
    -rw-r--r-- 1 root root 9.3G May 17 13:14 backup_2023_05_17T12_38_40.sql.gz
    -rw-r--r-- 1 root root 9.3G Apr 18 19:15 backup_2023_04_18T18_41_00.sql.gz
    -rw-r--r-- 1 root root 8.0G Apr  3 07:51 backup_2023_04_03T07_22_10.sql.gz
    ```

### Copying all backup files out of `docker`

Again assuming default configurations, to copy backup files out of the `postgres` `docker` `container` to a `backups` folder in the working directory of your local filesystem (assuming logged in as `user`): 

=== "user"

    ```console
    docker cp $(docker compose -f local.yml ps -q postgres):backups backups
    Successfully copied 28.5GB to /home/user/lwmdb/backups
    ```

=== "sudo"

    ```console
    sudo docker cp $(sudo docker compose -f local.yml ps -q postgres):backups backups
    Successfully copied 28.5GB to /home/user/lwmdb/backups
    ```

### Copying one backup file out of `docker`

To simply copy one backup (`backup_2023_05_17T12_38_40.sql.gz` in this case) database file (rather than all) to a local `backups` folder

=== "user"

    ```console
    docker cp $(docker compose -f local.yml ps -q postgres):backups/backup_2023_05_17T12_38_40.sql.gz backups/
    ```

=== "sudo"

    ```console
    sudo docker cp $(sudo docker compose -f local.yml ps -q postgres):backups/backup_2023_05_17T12_38_40.sql.gz backups/
    ```

#### Database configuration

It is possible to name the database something other thatn `lwmdb` if needed, and that can be helpful if needed to make a schema change and wanting to copy the schema to manage that process. 

The name of the database schema is specified in local `.env/local` and `.env/production` [`env`](https://docs.docker.com/compose/environment-variables/env-file/) files. The default `.env/local` includes

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=lwmdb
POSTGRES_USER=lwmdb
...
```

The name of the database is separate from the names of the tables so, for example, you can replace the `POSTGRES_DB` and `POSTGRES_USER` with your preferred configuration. This works because each of the models in this project (for example [`newspapers.Item`](/reference/newspapers/models/#newspapers.models.Item))


!!! warning

    It is *strongly advised* to keep `.env/production` and `.env/local` database configurations the same for testing purposes. 
