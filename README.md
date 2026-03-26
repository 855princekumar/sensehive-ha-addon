# SenseHive Home Assistant Add-ons

Home Assistant add-ons for running SenseHive - a lightweight MQTT dashboard and logger - directly inside your Home Assistant environment.

---

## What is SenseHive?

SenseHive is a self-hosted tool to:

- Debug raw MQTT data  
- Log messages automatically  
- Visualize real-time device data  
- Export data as CSV  

It is designed as a lightweight alternative to heavier IoT stacks.

---

## Available Add-ons

This repository provides two add-ons based on system architecture:

### SenseHive (ARM / Raspberry Pi)
- For Raspberry Pi and ARM-based systems  
- Uses image: `devprincekumar/sense-hive:arm-pi5`

### SenseHive (AMD64)
- For Intel / AMD systems  
- Uses image: `devprincekumar/sense-hive:latest`

---

## Installation

1. Open Home Assistant  
2. Go to **Settings → Add-ons → Add-on Store**  
3. Click the menu (⋮) → **Repositories**  
4. Add this repository:
