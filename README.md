# Caregiver Stress Prediction using Wearable Sensor Data

## 📌 Project Overview

This project analyzes physiological and motion sensor data collected from caregivers using wearable devices. The system predicts caregiver stress levels and presents insights using an interactive visual analytics dashboard.

The application is developed using FastAPI (backend), Streamlit (frontend), and SQLite (database). It also includes a conversational chatbot that helps users explore data and understand trends.

---

## 🎯 Project Objectives

* Design a user-friendly interactive dashboard
* Analyze wearable sensor data to identify stress patterns
* Visualize trends using multiple coordinated charts
* Support decision-making through data insights
* Integrate a chatbot to guide users and explain results

---

## 🏥 Problem Domain

**Domain:** Healthcare
**Focus Area:** Caregiver Stress Monitoring

Caregivers often experience stress due to heavy workload and continuous responsibilities. Monitoring physiological signals helps detect stress early and supports better healthcare management.

---

## 📊 Dataset Description

The dataset contains physiological and motion sensor data collected from wearable devices.

### Variables Description

| Variable          | Description                                    | Data Type   |
| ----------------- | ---------------------------------------------- | ----------- |
| id                | Unique record ID                               | Integer     |
| date              | Date of recording                              | Date        |
| time              | Time of recording                              | Time        |
| datetime          | Combined date and time                         | DateTime    |
| X                 | Movement along X-axis                          | Numeric     |
| Y                 | Movement along Y-axis                          | Numeric     |
| Z                 | Movement along Z-axis                          | Numeric     |
| MovementMagnitude | Overall movement intensity                     | Numeric     |
| EDA               | Electrodermal Activity (stress-related signal) | Numeric     |
| HR                | Heart Rate (beats per minute)                  | Numeric     |
| TEMP              | Body Temperature                               | Numeric     |
| label             | Stress Level (Low / Medium / High)             | Categorical |

This dataset supports multi-dimensional analysis, comparisons, and trend visualization.

## 🖥️ Technologies Used

**Backend:**

* Python
* FastAPI

**Frontend:**

* Streamlit

**Database:**

* SQLite

**Visualization:**

* Matplotlib
* Seaborn
* Plotly

**Chatbot:**

* LLM-powered conversational agent

---

## 🤖 Chatbot Features

The system includes an intelligent chatbot that allows users to:

* Ask questions about stress patterns
* Explore dataset insights
* Understand trends shown in charts
* Identify unusual stress patterns
* Support decision-making based on data

---

## 👥 Team Responsibilities

Each team member is responsible for specific sensor analysis:

* **MovementMagnitude** - Harishalinee Elangovan(IT22057488)
* **EDA** - Kaushalya Nagenthraraja(IT22289384)
* **HR** - Dayana Priyadharshani Kumar(IT22178640)
* **TEMP** - Vidursha Prabagaran(IT22294098)

---
## 🎨 User Persona

**Target User:** Healthcare Manager / Caregiver Supervisor

The dashboard is designed to help users monitor caregiver stress levels, identify workload patterns, and support healthcare planning decisions.

---

## 📌 Conclusion

This project demonstrates how wearable sensor data, interactive dashboards, and conversational analytics can be combined to monitor caregiver stress levels. The system supports data-driven decision-making and improves understanding of caregiver workload and stress patterns.

