# Simulate 4: Rainwater Pit Monitoring System

## Introduction
Simulate 4 is a comprehensive solution for monitoring the water level in rainwater pits. Utilizing an ESP-32 paired with an ultrasonic meter, this project measures the empty space in a pit, calculates the water level, and communicates the data using MQTT. The data is then processed and stored using Node-RED and MariaDB on a Raspberry Pi Zero. The goal is to provide an easily accessible visual representation of the water level in the pit, ultimately aiming to support both web and mobile platforms for visualization.

## System Architecture
- **ESP-32 with Ultrasonic Meter**: Measures the empty space in the rainwater pit.
- **MQTT Protocol**: Facilitates the transmission of measurement data from the ESP-32 to the Node-RED environment.
- **Node-RED**: Running on Raspberry Pi Zero, it processes incoming data and inserts it into the database.
- **MariaDB**: Hosted on Raspberry Pi Zero, it stores the measurement data in two tables - one for the meter UUID and rainwater pit measurements, and another for the measurements sent from the ESP-32 with a Foreign Key to the meter's ID.
- **Web Visualization**: A web interface displays the rainwater pit's water level dynamically.

## Installation

### Hardware Requirements
- ESP-32
- Ultrasonic Meter
- Raspberry Pi Zero

### Software Requirements
- Node-RED
- MariaDB
- MQTT Broker (e.g., Mosquitto)

### Setup Guide
1. **ESP-32 Configuration**: Flash your ESP-32 with the provided firmware to measure the distance using the ultrasonic meter and send the data via MQTT.
2. **MQTT Broker Setup**: Install and configure Mosquitto on your Raspberry Pi Zero or any other server to handle MQTT messages.
3. **Node-RED Installation**: Ensure Node-RED is set up on your Raspberry Pi Zero, including the necessary flows to receive MQTT data and insert it into MariaDB.
4. **Database Configuration**: Set up MariaDB on your Raspberry Pi Zero, creating the required tables for storing meter and measurement data.

## Usage
After completing the installation, the system will automatically measure the rainwater pit's water level and update the database at specified intervals. To view the current water level, access the web interface hosted on your Raspberry Pi Zero.

## Future Work
- **Enhanced Visualization**: Improving the web interface to offer more detailed insights into water level trends over time.
- **Mobile App Development**: Creating a mobile application to provide convenient access to rainwater pit measurements on the go.

## Acknowledgments
- Thanks to everyone who has contributed to the development and testing of Simulate 4.
- Special thanks to the open-source community for providing the tools and libraries that make this project possible.
