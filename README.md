# Raspberry Pi LED Control System

This project consists of two parts:
1. A Raspberry Pi script (`main.py`) that controls 4 LEDs via relay modules by reading their status from MongoDB
2. A web interface to control the LEDs by updating their state in the MongoDB database

## Setup Instructions

### Prerequisites
- Raspberry Pi with Python installed
- 4 LEDs connected to GPIO pins via relay module
  - LED 1: GPIO 17
  - LED 2: GPIO 27
  - LED 3: GPIO 22
  - LED 4: GPIO 18
- MongoDB Atlas account (already configured in the code)
- Internet connection for the Raspberry Pi

### Installation

1. Clone this repository to your Raspberry Pi
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Application

1. Run the main controller script on your Raspberry Pi:
   ```
   python main.py
   ```
   This script will connect to MongoDB and control the LEDs based on their state in the database.

2. In a separate terminal or on another machine, run the Flask web application:
   ```
   python app.py
   ```
   This will start a web server on port 5000.

3. Access the web interface by navigating to:
   ```
   http://your-raspberry-pi-ip:5000
   ```
   (Replace `your-raspberry-pi-ip` with the actual IP address of your Pi)

## How It Works

1. The web interface displays controls for 4 LEDs
2. When you toggle an LED state in the web interface, it updates the MongoDB database
3. The Raspberry Pi script (`main.py`) continuously listens for changes to the MongoDB database
4. When a change is detected, `main.py` updates the corresponding GPIO pin to turn the LED on or off through the relay

## Features

- Individual control of each LED
- "Turn All ON" and "Turn All OFF" buttons for controlling all LEDs at once
- Automatic updates with 5-second refresh interval
- Manual refresh option
- Visual indication of LED states

## Troubleshooting

- If the LEDs don't respond, check that `main.py` is running on the Raspberry Pi
- Ensure your MongoDB connection string is correct and accessible from both applications
- Verify that the GPIO pins are correctly connected to your relay module
- Check your relay module's logic (some relay modules are active-low)

## Security Note

This example uses a hardcoded MongoDB connection string for simplicity. In a production environment, you should use environment variables or a secure configuration file to store sensitive information. 