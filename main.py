import os
import psutil
import datetime
import logging
from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from wakeonlan import send_magic_packet
from starlette.status import HTTP_403_FORBIDDEN

# ==========================================
# CONFIGURATION SECTION
# ==========================================

# Security: The API Key required for all requests.
# Clients must send this in the header "x-api-key".
API_KEY = "DFAS-api"
API_KEY_HEADER_NAME = "x-api-key"

# Network: Host 0.0.0.0 makes it accessible on the local network.
HOST = "0.0.0.0"
PORT = 8000

# Logging: Save logs to a file and print to console
LOG_DIR = "Logs"
LOG_FILE = "dfas_server.log"

# Create Logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, LOG_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'), # Save to file
        logging.StreamHandler()         # Print to console
    ]
)
logger = logging.getLogger("DFAS-Server")

# ==========================================
# SETUP & MIDDLEWARE
# ==========================================

app = FastAPI(
    title="DFAS-Server",
    description="Python Backend for Android Admin Launcher",
    version="2.1.0"
)

# CORS: Allow all origins so the Android emulator or devices on LAN can connect easily.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Scheme
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency that validates the x-api-key header.
    Returns 403 Forbidden if invalid or missing.
    """
    if api_key == API_KEY:
        return api_key
    else:
        logger.warning(f"Unauthorized access attempt. Key provided: {api_key}")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )

# ==========================================
# DATA MODELS (Pydantic)
# ==========================================

class DiskInfo(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float

class NetInfo(BaseModel):
    bytes_sent_mb: float
    bytes_recv_mb: float

class SystemStatus(BaseModel):
    status: str
    uptime: str
    cpu_percent: float
    cpu_freq_current: float
    ram_percent: float
    ram_total_gb: float
    ram_used_gb: float
    disk_c: DiskInfo
    network: NetInfo
    battery_percent: float | None = None
    is_plugged_in: bool | None = None

class WolRequest(BaseModel):
    mac_address: str

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_uptime_string():
    """Calculates system uptime in a human-readable format."""
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    now = datetime.datetime.now()
    uptime = now - boot_time
    # Remove microseconds for cleaner output
    return str(uptime).split('.')[0]

def bytes_to_gb(bytes_value):
    return round(bytes_value / (1024 ** 3), 2)

def bytes_to_mb(bytes_value):
    return round(bytes_value / (1024 ** 2), 2)

# ==========================================
# API ENDPOINTS
# ==========================================

@app.get("/status", response_model=SystemStatus, tags=["System"])
async def get_status(auth: str = Depends(verify_api_key)):
    """
    Returns detailed system statistics: CPU, RAM, Disk, Network, Battery.
    """
    try:
        # 1. CPU
        cpu_pct = psutil.cpu_percent(interval=0.1) # Short interval for responsiveness
        cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0.0

        # 2. RAM
        mem = psutil.virtual_memory()

        # 3. Disk (C:)
        # Adjust path if running on Linux ('/') or Mac ('/')
        disk_path = 'C:\\' if os.name == 'nt' else '/'
        disk = psutil.disk_usage(disk_path)

        # 4. Network (Since boot)
        net = psutil.net_io_counters()

        # 5. Battery (Optional, for laptops)
        battery = psutil.sensors_battery()
        batt_pct = battery.percent if battery else None
        batt_plugged = battery.power_plugged if battery else None

        logger.info(f"Status requested. CPU: {cpu_pct}%, RAM: {mem.percent}%")

        return {
            "status": "online",
            "uptime": get_uptime_string(),
            "cpu_percent": cpu_pct,
            "cpu_freq_current": round(cpu_freq, 2),
            "ram_percent": mem.percent,
            "ram_total_gb": bytes_to_gb(mem.total),
            "ram_used_gb": bytes_to_gb(mem.used),
            "disk_c": {
                "total_gb": bytes_to_gb(disk.total),
                "used_gb": bytes_to_gb(disk.used),
                "free_gb": bytes_to_gb(disk.free),
                "percent": disk.percent
            },
            "network": {
                "bytes_sent_mb": bytes_to_mb(net.bytes_sent),
                "bytes_recv_mb": bytes_to_mb(net.bytes_recv)
            },
            "battery_percent": batt_pct,
            "is_plugged_in": batt_plugged
        }

    except Exception as e:
        logger.error(f"Error gathering stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/wol", tags=["Control"])
async def wake_on_lan(request: WolRequest, auth: str = Depends(verify_api_key)):
    """
    Sends a Wake-on-LAN 'Magic Packet' to the specified MAC address.
    """
    mac = request.mac_address
    try:
        send_magic_packet(mac)
        logger.info(f"WoL packet sent to {mac}")
        return {"status": "success", "message": f"Magic packet sent to {mac}"}
    except Exception as e:
        logger.error(f"Failed to send WoL to {mac}: {e}")
        raise HTTPException(status_code=500, detail=f"WoL Error: {e}")


if __name__ == "__main__":
    import uvicorn
    # Run the server
    print(f"--- DFAS Server Running on {HOST}:{PORT} ---")
    print(f"--- API Key: {API_KEY} ---")
    print(f"--- Logging to: {log_path} ---")
    uvicorn.run(app, host=HOST, port=PORT)
