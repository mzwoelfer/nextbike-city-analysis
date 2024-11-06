# Postgres tweaks - additional writeup

Postgres is not reachable by default via network.

1. Ensure postgres is running:
```SHELL
sudo systemctl status postgresql
```

2. COnfigure Postgres to accept remote connections:
```SHELL
vim /etc/postgresql/15/main/postgresql.conf

# Find the line: listen_addresses
# Change it to
listen_addresses = '*'

sudo vim /etc/postgresql/15/main/pg_hba.conf

# Add the following to the end of the file:
host	all		all		0.0.0.0/0		md5

# [OPTIONAL] Or restric traffic to your local network
host	all		all		192.168.22.0/24		md5
```

3. Restart Postgres
```SHELL
# Restart postgres
sudo systemctl restart postgresql
```
