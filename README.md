# Smart Energy Monitoring System

An IoT-based smart energy monitoring system developed for real-time electrical energy measurement, monitoring, and appliance classification.

## Overview

This project combines electrical energy measurement, embedded systems, web technologies, and machine learning in a single monitoring platform.

The system collects electrical parameters from connected loads using an ESP32 and PZEM-004T V3 energy monitoring module. The measured data is transmitted through Wi-Fi and displayed through a web-based interface.

A machine learning model is also used to classify connected electrical appliances based on their measured electrical characteristics.

## Features

- Real-time voltage measurement
- Current measurement
- Active power measurement
- Energy consumption monitoring
- Frequency measurement
- Power factor measurement
- Wi-Fi-based data communication
- Web-based monitoring interface
- Appliance classification using machine learning

## Hardware

- ESP32
- PZEM-004T V3
- HLK-PM01
- Fuse

## Software

- ESP32 Programming (C/C++)
- Python
- Machine Learning
- Random Forest

## System Architecture

| Stage | Component |
|---|---|
| 1 | Electrical Load |
| 2 | PZEM-004T V3 |
| 3 | ESP32 |
| 4 | Wi-Fi Communication |
| 5 | Web Interface |
| 6 | Machine Learning |
| 7 | Appliance Classification |

## Measured Parameters

| Parameter | Unit |
|---|---|
| Voltage | V |
| Current | A |
| Active Power | W |
| Energy | kWh |
| Frequency | Hz |
| Power Factor | - |

## Appliance Classification

The measured electrical data is processed by a machine learning model to classify connected electrical appliances.

The model uses electrical features such as:

- Voltage
- Current
- Active Power
- Power Factor

## Author

**İsmail Burak Canik**

Electrical & Electronics Engineer
