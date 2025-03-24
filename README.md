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

**Note** Please do not use this on BITS WIFI the database won't connect 

Below is an example of a structured README.md file in Markdown for your hackathon project:

---

# Hackathon Project

This project consists of three main parts:
## Overview

This project is a hackathon submission that integrates a modern Next.js frontend, a Python backend, and a PostgreSQL database hosted on AWS RDS. The frontend communicates with the backend through API endpoints, while the backend interacts with the PostgreSQL database to manage data.

## Architecture

- **Frontend:**  
  Uses Next.js to render dynamic web pages and provide a smooth user experience.

- **Backend:**  
  A Python server that handles business logic and API endpoints. All required dependencies are listed in a `requirements.txt` file.

- **Database:**  
  AWS RDS PostgreSQL database accessed via standard SQL queries. Use a client like Postico for administration and manual query execution if needed.

## Prerequisites

- **Node.js & npm:**  
  [Download and install Node.js](https://nodejs.org/)

- **Python 3:**  
  Ensure Python 3 is installed on your system.

- **PostgreSQL Client:**  
  For example, [Postico](https://eggerapps.at/postico/) or any preferred client.

- **AWS RDS Setup:**  
  Ensure your AWS RDS instance is running and accessible.

## Installation

### Frontend Setup (Next.js)

1. **Clone the repository:**

   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>/frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Start the development server:**

   ```bash
   npm run dev
   ```

   The frontend server should now be running at [http://localhost:3000](http://localhost:3000).

### Backend Setup (Python)

1. **Navigate to the backend directory:**

   ```bash
   cd <your-repo-folder>/backend
   ```

2. **Set up a virtual environment (optional but recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file:**

   Create a file named `.env` in the backend directory with the following content:

   ```ini
   DATABASE_URL=postgresql://<username>:<password>@<your-aws-rds-endpoint>:<port>/<database_name>
   ```

5. **Start the backend server:**

   ```bash
   python3 main.py
   ```

### Database Setup (AWS RDS & PostgreSQL)

- Ensure your AWS RDS PostgreSQL instance is running.
- Use a PostgreSQL client (like Postico) to connect using the credentials provided in your `.env` file.
- Run the necessary SQL queries to set up tables and seed initial data. If you have an automated script or migration tool (e.g., Alembic, Flyway, or a custom script), run that to generate the required schema.

  **Example SQL Setup (if done manually):**

  ```sql
  CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      username VARCHAR(50) UNIQUE NOT NULL,
      email VARCHAR(100) UNIQUE NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS posts (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id),
      title VARCHAR(255) NOT NULL,
      content TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```

  > **Note:** If your project uses a migration tool, follow the tool's documentation to run migrations.

## Usage

### Running the Frontend

1. Navigate to the frontend directory.
2. Run:

   ```bash
   npm run dev
   ```

3. Open your browser and navigate to [http://localhost:3000](http://localhost:3000).

### Running the Backend

1. Navigate to the backend directory.
2. Activate your virtual environment (if using one).
3. Run:

   ```bash
   python3 main.py
   ```

## Database Queries

The backend may run queries automatically using an ORM or raw SQL scripts. If you need to manually run queries, you can use the provided SQL examples in the [Database Setup](#database-setup-aws-rds--postgresql) section. Some common queries include:

- **Select all users:**

  ```sql
  SELECT * FROM users;
  ```

- **Select posts for a user:**

  ```sql
  SELECT * FROM posts WHERE user_id = <user_id>;
  ```

## Environment Variables

For the backend, environment variables are stored in a `.env` file. The critical variable is:

- `DATABASE_URL`: Your PostgreSQL connection string.

## Contributing

Contributions are welcome! Please fork the repository and open a pull request with your changes.



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
