#!/bin/bash

# Stop on error
set -e

# Variables
GITHUB_REPO="https://github.com/zwoefler/nextbike-city-analysis.git"
DB_USER="bike_admin"
DB_PASSWORD="mybike"
DB_NAME="bikes"
INSTALL_DIR="/opt/nextbike-city-analysis"
VENV_DIR="$INSTALL_DIR/Env"
SCRIPT_DIR="$INSTALL_DIR/src/data-processing"
CONFIG_FILE="$SCRIPT_DIR/config.py"
CRON_JOB="* * * * * cd $INSTALL_DIR && source Env/bin/activate && python3 src/data-processing/query_bike_apis.py"

# 1. Update system and install dependencies
echo "Updating and installing system dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y git cron python3 python3-pip python3-venv postgresql postgresql-contrib

# 2. Configure IPv4 preference (optional for IPv6 environments)
echo "Configuring system to prefer IPv4..."
sudo sed -i '/precedence ::ffff:0:0\/96 100/s/^#//' /etc/gai.conf

# 3. Add bike_admin user and configure SSH
echo "Creating user $DB_USER and setting up SSH..."
sudo adduser --disabled-password --gecos "" $DB_USER
sudo usermod -aG sudo $DB_USER
sudo usermod -aG postgres $DB_USER
sudo mkdir -p /home/$DB_USER/.ssh
sudo cp ~/.ssh/authorized_keys /home/$DB_USER/.ssh/
sudo chown -R $DB_USER:$DB_USER /home/$DB_USER/.ssh
sudo chmod 700 /home/$DB_USER/.ssh
sudo chmod 600 /home/$DB_USER/.ssh/authorized_keys

# 4. Configure PostgreSQL and create database and user
echo "Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER CREATEDB SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# 5. Clone the repository to /opt and set permissions
echo "Cloning GitHub repository to /opt..."
sudo git clone $GITHUB_REPO $INSTALL_DIR
sudo chown -R $DB_USER:$DB_USER $INSTALL_DIR

# 6. Switch to bike_admin to finish setup
echo "Switching to $DB_USER for application setup..."
sudo -i -u $DB_USER bash <<EOF

# Set up Python virtual environment and install requirements
echo "Setting up Python virtual environment..."
cd $INSTALL_DIR
python3 -m venv Env
source Env/bin/activate
pip install -r /opt/nextbike-city-analysis/src/data-processing/requirements.txt

# Set up PostgreSQL schema
echo "Setting up PostgreSQL schema..."
psql -U $DB_USER -d $DB_NAME -f $INSTALL_DIR/src/sql-scripts/create_bikeDB.sql

# Configure config.py with database credentials
echo "Creating config.py with database credentials..."
cat <<CONFIG > $CONFIG_FILE
dbhost = 'localhost'
dbname = '$DB_NAME'
dbuser = '$DB_USER'
dbpassword = '$DB_PASSWORD'
CONFIG

# Test the data aggregation script
echo "Testing data aggregation script..."
source Env/bin/activate
python3 src/data-processing/query_bike_apis.py

# Set up cron job for automated data collection every minute
echo "Setting up cron job for data collection..."
(crontab -l; echo "$CRON_JOB") | crontab -

EOF

echo "Setup complete! Data collection should now run every minute."

