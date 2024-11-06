# Backup Postgres

## Back Up public Schema

As thee `bike_admin` user:
```SHELL
pg_dump -h localhost -U bike_admin -d bikes -n public -F c -f public_schema_backup.sql
```


## Restore public schema

As the `bike_admin` user:
```SHELL
pg_restore -h localhost -U bike_admin -d bikes_restored -F c public_schema_backup.sql
```
