# 🌡️ IoT Room Climate Dashboard 

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-092E20.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B.svg?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![ESP8266](https://img.shields.io/badge/Hardware-ESP8266-black.svg?logo=espressif&logoColor=white)](https://www.espressif.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

A real-time, full-stack IoT dashboard for monitoring and controlling room climate. This project bridges the gap between hardware and web interfaces, using an ESP8266 microcontroller to collect sensor data and a Django REST API to process, store, and visualize it beautifully.



## ✨ Features

* **Real-Time Telemetry:** Live temperature and humidity monitoring with zero-refresh UI updates.
* **Smart Automation:** Configurable temperature thresholds (High/Low) that automatically trigger an exhaust fan or AC via a relay.
* **Manual Override:** Seamlessly toggle between "Auto" and "Manual" control modes directly from the web interface.
* **Interactive Analytics:** Dynamic, time-series charts (powered by Chart.js) visualizing historical data across 1-hour, 24-hour, and 7-day spans.
* **Daily Aggregations:** Automated daily logs tracking average/min/max temperatures and total fan runtime.
* **Robust API Engine:** Scalable Django REST Framework backend coupled with MongoDB for high-frequency telemetry ingestion.

## 🛠️ Tech Stack

**Frontend**
* HTML5 / CSS3 / Vanilla JS
* Bootstrap 5 (Responsive Layout)
* Chart.js (Data Visualization)
* FontAwesome (Iconography)

**Backend & Database**
* Django & Django REST Framework (DRF)
* PyMongo (MongoDB integration)
* SQLite (Django Admin/Auth)

**Hardware**
* ESP8266 (NodeMCU)
* DHT22 Temperature & Humidity Sensor
* 5V Relay Module

## 🔌 Hardware Setup

1. **DHT22 Sensor:** Connect data pin to `GPIO2` (`D4`).
2. **Relay Module:** Connect signal pin to `GPIO5` (`D1`).
3. **Power:** Provide 3.3V/5V to components as required and share a common ground.

*Ensure you update the WiFi credentials and Server IP in the `esp8266_code/iot_device.ino` file before flashing.*

## 🚀 Installation & Local Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/iot_dashboard.git](https://github.com/yourusername/iot_dashboard.git)
cd iot_dashboard
