# Postgres tweaks - additional writeup

Postgres is not reachable by default via network.

1. Ensure postgres is running:
```SHELL
sudo systemctl status postgresql
```

2. COnfigure Postgres to accept remote connections:
```SHELL
# Change listen_addresses = 'localhost' to '*' in /etc/postgresql/15/main/postgresql.conf
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/15/main/postgresql.conf

# Add the following to the end of the file:
# host	all		all		0.0.0.0/0		md5
echo "host	all		all		0.0.0.0/0		md5" | sudo tee -a /etc/postgresql/15/main/pg_hba.conf
# [OPTIONAL] Or restric traffic to your local network
# host	all		all		192.168.22.0/24		md5
```

3. Restart Postgres
```SHELL
# Restart postgres
sudo systemctl restart postgresql
```
