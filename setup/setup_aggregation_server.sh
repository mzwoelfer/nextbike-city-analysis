#!/bin/bash

# Stop on error
set -e

# Variables
GITHUB_REPO="https://github.com/zwoefler/nextbike-city-analysis.git"
DB_USER="bike_admin"
DB_PASSWORD="mybike"
DB_NAME="nextbike_data"
INSTALL_DIR="/opt/nextbike-city-analysis"
VENV_DIR="$INSTALL_DIR/Env"
CONFIG_FILE="$INSTALL_DIR/src/config.py"
CRON_JOB="* * * * * cd $INSTALL_DIR && $INSTALL_DIR/Env/bin/python3 src/query_nextbike.py"

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

# 4. Clone the repository to /opt and set permissions
echo "Cloning GitHub repository to /opt..."
sudo git clone $GITHUB_REPO $INSTALL_DIR
sudo chown -R $DB_USER:$DB_USER $INSTALL_DIR

# 5. Configure PostgreSQL and create database and user
echo "Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER CREATEDB SUPERUSER;"
sudo -u postgres psql -f $INSTALL_DIR/src/create_bike_and_stations_db.sql

# 6. Switch to bike_admin to finish setup
echo "Switching to $DB_USER for application setup..."
sudo -i -u $DB_USER bash <<EOF

# Set up Python virtual environment and install requirements
echo "Setup Python virtual environment..."
cd $INSTALL_DIR
python3 -m venv Env
source Env/bin/activate
pip install -r $INSTALL_DIR/requirements.txt

# Configure config.py with database credentials
echo "Creating config.py with database credentials..."
cat <<CONFIG > $CONFIG_FILE
dbhost = 'localhost'
dbname = '$DB_NAME'
dbuser = '$DB_USER'
dbpassword = '$DB_PASSWORD'
CONFIG

echo "Testing data aggregation script..."
python3 $INSTALL_DIR/src/query_nextbike.py

# Set up cron job for automated data collection every minute
echo "Setting up cron job for data collection..."
(crontab -l; echo "$CRON_JOB") | crontab -

EOF

echo "Setup complete! Data collection should now run every minute."

