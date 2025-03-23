# Raven: Characterization of Delays in Packet Transmission

**Hackathon Name:** Hackenza  
**Status:** Completed  
**Frontend:** Next.js  
**Backend:** FastAPI  
**Database:** PostgreSQL  

## Table of Contents
- [Introduction](#introduction)
- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [System Architecture](#system-architecture)
- [Setup and Installation](#setup-and-installation)
- [Limitations](#limitations)
- [Future Optimizations](#future-optimizations)
- [Team Members](#team-members)
- [License](#license)

---

## Introduction
**Raven** is an end-to-end GUI-based platform designed to analyze network packet delays in IoT and cloud-based applications. The system allows users to upload `.pcapng` files and provides detailed insights into packet transmission delays, including latency, anomalies, and delay categorization. The goal is to enhance network performance analysis and optimize data transmission efficiency, particularly for time-sensitive applications like health monitoring and IoT systems.

---

## Problem Statement
Modern IoT and cloud-based applications often suffer from network delays at various stages, such as broker processing, retransmission, and cloud uploads. These delays can degrade system efficiency, leading to packet loss and increased latency. Raven addresses this issue by providing a comprehensive analysis of packet delays, helping users identify and mitigate performance bottlenecks.

---

## Solution Overview
Raven is a full-stack application that provides detailed analysis of network packets. Users can upload `.pcapng` files and receive visually intuitive graphical insights. The system is divided into three main components:

### 1. Frontend
- Built with **Next.js** (React Framework) for a responsive and dynamic user interface.
- Styled using **TailwindCSS** for efficient UI development.
- Utilizes **ShadCN** for prebuilt UI components, forms, and customizable charts.

### 2. Backend
- **FastAPI** (Python) for handling requests and responses with minimal latency.
- Microservices architecture for specialized packet analysis:
  - **Latency Service**: Measures network transmission delays.
  - **Delay Service**: Analyzes packet delays.
  - **Packet Analysis Service**: Processes and classifies packet metadata.
  - **Protocol Service**: Classifies packets based on their protocol.
- **PostgreSQL** for database management.
- **Redis** for caching to reduce query times.
- **Nginx** as a load balancer for efficient request routing.

### 3. Database
- **PostgreSQL** is used to store packet metadata, delay categorization, latency analysis, and anomaly detection results.
- Cached results are stored in **Redis** for fast retrieval.

---

## Features
- **File Upload**: Users can upload `.pcapng` files for analysis.
- **Delay Categorization**: Analyzes and categorizes packet delays.
- **Latency Analysis**: Measures average, maximum, and minimum latency.
- **Anomaly Detection**: Identifies and classifies anomalies in packet transmission.
- **Data Visualization**: Presents analysis results through interactive charts and graphs.
- **Caching**: Uses Redis to cache results for faster retrieval.

---

## Technologies Used

### Frontend
- Next.js
- TailwindCSS
- ShadCN

### Backend
- FastAPI (Python)
- PostgreSQL
- Redis
- Nginx

### Other Tools
- Postman (API Testing)
- Git/GitHub (Version Control)

---

## System Architecture
The system architecture is designed for scalability and efficiency:

1. **Client Request Handling**: Requests are routed through a load balancer (Nginx) for even traffic distribution.
2. **Backend API & Caching**: Redis checks for cached results before forwarding requests to the backend.
3. **Microservices Processing**: Specialized microservices handle different aspects of packet analysis.
4. **Database Storage**: Results are stored in PostgreSQL, with Redis caching for fast retrieval.

### Database Schema
- **Packet Metadata**: Stores packet details such as ID, timestamp, protocol, source IP, destination IP, and packet size.
- **Delay Categorization**: Categorizes delays for each packet.
- **Latency Analysis**: Stores average, maximum, and minimum latency values.
- **Anomaly Detection**: Identifies and classifies anomalies in packet transmission.

---

## Setup and Installation

### Prerequisites
- Node.js and npm installed
- Python 3.9 or later
- PostgreSQL installed and running
- Redis installed and running

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/raven.git
   ```
2. **Navigate to the project directory**:
   ```bash
   cd raven
   ```
3. **Install frontend dependencies**:
   ```bash
   cd client
   npm install
   ```
4. **Install backend dependencies**:
   ```bash
   cd ../server
   pip install -r requirements.txt
   ```
5. **Set up environment variables**:
   Create a `.env` file in the `server` directory and add the following:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   REDIS_URL=redis://localhost:6379
   ```
6. **Run the backend server**:
   ```bash
   python main.py
   ```
7. **Run the frontend**:
   ```bash
   cd ../client
   npm start
   ```
8. **Access the application**:
   Open your browser and go to `http://localhost:3000`.

---

## Limitations
- **Single Point of Failure**: Only one backend API server is running.
- **Database Replication**: No database replication; failure will bring the system down.
- **Scalability**: The load balancer is not auto-scalable.
- **Computation Speed**: The system may slow down with a large number of packets.
- **File Handling**: Only one `.pcapng` file can be analyzed at a time.

---

## Future Optimizations
- **Low-Level Languages**: Use Rust or other low-level languages for faster computation.
- **Scalability**: Deploy multiple servers on AWS EC2 instances to handle high traffic.
- **Database Optimization**: Store packets in a more efficient format for faster CRUD operations.
- **Multi-Threading**: Handle multiple `.pcapng` files simultaneously using a multi-threaded workflow.

---

## Team Members
- **Pratyush Harigovind** (2022B5AA0255G)
- **Barnamoy Roy** (2022B5AA0916G)
- **Shashwat Gupta** (2022B5A80925G)
- **Shivam Agarwala** (2022B3A70110G)

---
