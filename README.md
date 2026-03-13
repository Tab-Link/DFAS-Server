# DFAS-Server

A production-ready **FastAPI** backend designed to control a Windows PC via an Android Admin Launcher.

## Features

*   **Real-time System Monitoring**:
    *   **CPU**: Usage (%) and Frequency.
    *   **RAM**: Used, Total, and Percentage.
    *   **Disk**: Drive C: status.
    *   **Network**: Data sent/received since boot.
    *   **Battery**: Level and charging status (for laptops).
    *   **Uptime**: System uptime in a readable format.
*   **Remote Control**:
    *   **Wake-on-LAN (WoL)**: Send Magic Packets to wake other devices on the network.
*   **Security**:
    *   API Key authentication (`x-api-key` header).
*   **Logging**:
    *   Logs are saved to `Logs/dfas_server.log` and printed to the console.

## Prerequisites

*   **Python 3.8+** installed on Windows.
*   **Ethernet connection** is recommended for Wake-on-LAN functionality.

## Installation

1.  **Clone or Download** this repository.
2.  Open a terminal (Command Prompt or PowerShell) in the project folder.
3.  Install the required Python libraries:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

You can configure the server settings directly in `main.py` (look for the **CONFIGURATION SECTION** at the top):

```python
# Security: The API Key required for all requests.
API_KEY = "DFAS-api"  # Change this to your preferred password

# Network: Host 0.0.0.0 makes it accessible on the local network.
HOST = "0.0.0.0"
PORT = 8000
```

## Usage

Run the server using the following command:

```bash
python main.py
```

You should see output indicating the server is running:

```text
--- DFAS Server Running on 0.0.0.0:8000 ---
--- API Key: DFAS-api ---
--- Logging to: Logs\dfas_server.log ---
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## API Endpoints

### 1. Get System Status

*   **URL**: `/status`
*   **Method**: `GET`
*   **Headers**:
    *   `x-api-key`: `DFAS-api` (or your configured key)
*   **Response**:

    ```json
    {
      "status": "online",
      "uptime": "2 days, 4:15:30",
      "cpu_percent": 12.5,
      "cpu_freq_current": 3600.0,
      "ram_percent": 45.2,
      "ram_total_gb": 16.0,
      "ram_used_gb": 7.23,
      "disk_c": {
        "total_gb": 500.0,
        "used_gb": 250.0,
        "free_gb": 250.0,
        "percent": 50.0
      },
      "network": {
        "bytes_sent_mb": 150.5,
        "bytes_recv_mb": 1024.2
      },
      "battery_percent": 98,
      "is_plugged_in": true
    }
    ```

### 2. Send Wake-on-LAN Packet

*   **URL**: `/wol`
*   **Method**: `POST`
*   **Headers**:
    *   `x-api-key`: `DFAS-api`
    *   `Content-Type`: `application/json`
*   **Body**:

    ```json
    {
      "mac_address": "AA:BB:CC:DD:EE:FF"
    }
    ```

## Troubleshooting

### Connection Timed Out / Connection Refused
If you cannot connect from your Android device:
1.  **Check IP**: Ensure you are using the correct Local IP of your PC (run `ipconfig` in terminal).
2.  **Firewall**: Windows Firewall might be blocking port `8000`.
    *   Allow `python.exe` through the firewall.
    *   Or create an Inbound Rule for TCP Port `8000`.

### Wake-on-LAN not working
1.  Ensure the target PC is connected via **Ethernet (LAN cable)**.
2.  Enable **Wake-on-LAN** in the target PC's **BIOS/UEFI**.
3.  Enable "Allow this device to wake the computer" in Windows Device Manager (Network Adapter properties).
