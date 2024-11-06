# Nextbike Data Aggregation Setup
Configure a Debian Server to continuously collect and store data from the Nextbike API every minute, ready for analysis.

Use the [script](setup_aggregation_server.sh) for a Debian server, or follow the [manual instructions](#setup-your-aggregation-server-manually) below.

#### Overview
- Create a database
- Setup the data gathering on a server
- Run script automated with a cron job


## Prerequisites
VM running Debian or Ubuntu with root/sudo access.

> Note: IPv4 is required as GitHub and Nextbike do not support IPv6.

Requirements for Debian Server:
- 50GB storage (Enough to scrape data for roughly 11 months. See [Notes](#notes))
- 2 CPU >1.8GHz
- 2 GB RAM


## Install using the script
1. Log into the VM: Access your VM via SSH as the root or a sudo-enabled user
2. Run the Setup Script directly from GitHub
```SHELL
curl -sSL https://raw.githubusercontent.com/zwoefler/nextbike-city-analysis/refs/heads/master/setup/setup_aggregation_server.sh | sudo bash
```

The script:
- Updates the system
- Installs required dependencies (git, cron, python3, python3-venv, postgresql)
- Creates the `bike_admin` user with necessary permissions.
- Configures PostgreSQL: Creates a database and grants access.
- Clones the Nextbike analysis repository to `/opt`.
- Sets up a Python virtual environment and install python dependencies.
- Configures the database schema and create the config.py file with credentials.
- Schedules a cron job to collect data every minute.

## Setup your aggregation server manually
1. Initial Server Setup and User Config
```SHELL
# 1. Create user `bike_admin` and add to sudo group
sudo adduser bike_admin
sudo usermod -aG sudo bike_admin

# 2. [OPTIONAL] When you are only root on a server, copy the ssh config:
sudo mkdir -p /home/bike_admin/.ssh
sudo cp ~/.ssh/authorized_keys /home/bike_admin/.ssh/
sudo chown -R bike_admin:bike_admin /home/bike_admin/.ssh
sudo chmod 700 /home/bike_admin/.ssh
sudo chmod 600 /home/bike_admin/.ssh/authorized_keys

# 3. [OPTIONAL] Secure SSH Configuration (recommended for security):
# Disable password authentication in /etc/ssh/sshd_config :

sudo vim /etc/ssh/sshd_config
# Set PasswordAuthentication no

# Then restart SSH:
sudo systemctl restart ssh
```


2. Install requirements
```SHELL
# Update machine
sudo apt update && sudo apt upgrade -y

# Install python3 + pip
sudo apt install python3 python3-pip python3-venv -y

# Install postgres
sudo apt install postgresql postgresql-contrib -y
```

3. Add `bike_admin` to postgres group:
```SHELL
sudo usermod -aG postgres bike_admin
```

4. Switch to user `bike_admin`:
```SHELL
sudo -i -u bike_admin
```

5. Configure the System to Prefer IPv4 (to avoid IPv6-only issues):
```SHELL
# Edit /etc/gai.conf

sudo vim /etc/gai.conf
# Uncomment this line:
precedence ::ffff:0:0/96 100
```

6. Setup Postgres Database
```SHELL
# Create bike_admin user
sudo -u postgres psql -c "CREATE USER bike_admin WITH ENCRYPTED PASSWORD 'mybike';"

# Give bike_admin privileges!
sudo -u postgres psql -c "ALTER ROLE bike_admin CREATEDB SUPERUSER;"

# Download Git repo:
git clone https://github.com/zwoefler/nextbike-city-analysis.git /opt/nextbike-city-analysis
sudo chown -R bike_admin:bike_admin /opt/nextbike-city-analysis

# Create the Database
psql -U bike_admin -d postgres -f /opt/nextbike-city-analysis/src/create_bikeDB.sql
```

7. Configure Data Automation: Fill out `/opt/nextbike-city-analysis/src/config.py`:
```Python
dbhost = "localhost"
dbname = "bikes"
dbuser = "bike_admin"
dbpassword = "mybike"
```

8. Make sure automation runs smoothly:
```SHELL
cd /opt/nextbike-city-analysis
python3 -m venv Env
source Env/bin/activate

pip install -r requirements.txt

cd src/
python3 query_bike_apis.py
```

9. Create a cronjob to run every minute:
```SHELL
# Edit crontab
crontab -e

# And type the following
* * * * * cd /opt/nextbike-city-analysis && /opt/nextbike-city-analysis/Env/bin/python3 src/query_bike_apis.py
```


## Notes
- IPV4 Requirement: Both GitHub and the Nextbike API require IPv4 connectivity.
- Data Storage: The database grows over time, roughly **400 lines** and **100KB per minute**.
144MB / day or 52,6GB / year

