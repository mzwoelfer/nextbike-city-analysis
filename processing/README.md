# Analyzing Nextbike data

Extract Nextbike trips from the postgres databases.

## Get trips data
1. Setup your environment
```SHELL
# Set variables
city_id=467
date='2024-12-21'

# Install requirements
python3 -m venv Env
source Env/bin/activate
pip install -r requirements.txt

# Copy the fake env vars
cp .env.example .env
```

2. Get your trips data
```SHELL
python3 -m nextbike_processing.main --city-id $city_id --export-folder ../data/trips_data/ --date $date
```

3. Trips data in `<PROJECT_ROOT>/data/trips_data/`


## Get data from postgres server
If your postgres is running on a server, add the following to your `~/.ssh/config`
```SHELL
Host nextbike_postgres
  HostName <YOUR SERVER IP>
  user <USER>
  Port 22
  IdentityFile <PATH TO SSH KEY>
```

Should your VMs have restrictions on ports, to pull the data from postgres, use SSH forwarding:

```SHELL
ssh -f -L 5432:localhost:5432 <USER>@<YOUR SERVER IP> -N
```

- `-f`: SSH in background after authentication
- `-L 5432:localhost:5432`: Forwards port 5432 from the remote host to your local machine
- `-N`: SSH doesn’t execute commands, useful for port forwarding only