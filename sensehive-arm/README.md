# SenseHive (ARM / Raspberry Pi)

SenseHive is a lightweight, self-hosted MQTT dashboard and logger designed for quick visibility into your IoT data.

It helps you debug, monitor, and store MQTT messages without requiring heavy tools like Grafana or InfluxDB.

---

## Features

- Real-time MQTT data visualization  
- Automatic topic-based logging (SQLite)  
- CSV export per topic  
- One-command deployment  
- Optimized for Raspberry Pi and low-spec devices  

---

## Why use this?

Home Assistant is excellent for automation and dashboards, but:

- Debugging raw MQTT topics can be difficult  
- Long-term raw logging is limited  
- Setting up full observability stacks can be overkill  

SenseHive provides a simple way to:

- Inspect MQTT data in real time  
- Log messages automatically  
- Export data for analysis  

---

## How it works

SenseHive connects to your existing MQTT broker (e.g., Mosquitto in Home Assistant).

---

## Configuration

After starting the add-on:

1. Open the Web UI  
2. Enter your MQTT broker details:
   - Host: your Home Assistant IP  
   - Port: 1883  
   - Username / Password (if configured)  

3. Add topics and start monitoring  

---

## Access

Once started, open:

http://homeassistant.local:5000  
or  
http://YOUR_HA_IP:5000  

---

## Notes

- This add-on does not replace Home Assistant  
- It complements MQTT debugging and logging workflows  

---

## Future Improvements

- Native Home Assistant integration  
- Retention policies  
- Performance optimizations  

---