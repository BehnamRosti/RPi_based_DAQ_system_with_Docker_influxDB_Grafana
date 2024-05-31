# Raspberry Pi based DAQ system using Docker, influxDB, and Grafana
In this totourial, one can follow steps required to make a real-time visualization of data recorded by Raspberry Pi and IoT Sensors. To achieve the goal of recording data from sensors connected to the Raspberry Pi, sending data to InfluxDB, and visualizing it with Grafana, Docker containers can streamline this process. Achieving real-time visualization of monitoring data can be accomplished by following steps.

## 1.	Install Docker on the Raspberry Pi
```bash
sudo apt-get update
sudo apt-get upgrade
curl -sSL https://get.docker.com | sh
```

```bash
# Add "YOUR_PI_USER" to the docker group:
sudo usermod -aG docker YOUR_PI_USER
sudo apt-get install -y libffi-dev libssl-dev
sudo apt-get install -y python3 python3-pip
```
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 2.	Write a Python application 
This file is required to read sensor data and send it to InfluxDB (see app.py)

## 3.	Package the Python application in a Docker image
3.1	Create a Dockerfile: Write a Dockerfile that specifies the environment and dependencies for your Python application (see Dockerfile)

3.2	Create a Requirements file: List all the dependencies of your Python application in a requirements.txt file (see requirements.txt)

## 4.	Create a Docker compose YAML file
This file is required to define how the Docker containers (Python app, InfluxDB, and Grafana) interact and are networked (see docker-compose.yml)

## 5.	Configure Grafana to Visualize Data
5.1	Access Grafana at http://[raspberry-pi-ip]:3000

```bash
# to see your Raspberry Pi IP
hostname -I
```

5.2	Login with admin/admin credentials

5.3	Add InfluxDB as a data source:

i.	URL: http://[raspberry-pi-ip]:8086

ii.	Database: sensordata (as defined in docker-compose.yml)

iii.	User/Password: admin/admin

5.4	Create a dashboard to visualize your sensor data

## License
[MIT](https://choosealicense.com/licenses/mit/)
