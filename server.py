"""
Pub & Bar Otomasyonu - FastAPI & WebSocket Merkezi Sunucu
--------------------------------------------------------
- iOS ve Android telefonlar için canlı bildirim dağıtımı
- Dinamik masa ve mekan düzenleme (Ekleme, Silme, İsim Değiştirme, Konumlandırma)
- Kamera görüntü işleme motoru (poc_test.py) ile çift yönlü entegrasyon
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn
import socket

app = FastAPI(title="Pub & Bar Otomasyonu Backend")

CONFIG_FILE = "layout_config.json"

# Varsayılan mekan ve masa düzeni
DEFAULT_CONFIG = {
    "zones": ["Ana Salon", "Bahçe", "VIP Loca", "Bar Tezgahı"],
    "tables": [
        {"id": "t1", "name": "Masa 1", "zone": "Ana Salon", "status": "active", "x": 30, "y": 40, "w": 85, "h": 85, "notes": "2x Bira (Tuborg Gold), 1x Fıstık", "last_alert": None, "alert_msg": ""},
        {"id": "t2", "name": "Masa 2", "zone": "Ana Salon", "status": "idle", "x": 140, "y": 40, "w": 85, "h": 85, "notes": "", "last_alert": None, "alert_msg": ""},
        {"id": "t3", "name": "Masa 3", "zone": "Ana Salon", "status": "active", "x": 250, "y": 40, "w": 85, "h": 85, "notes": "1x Viski Cola, 1x Cin Tonik", "last_alert": None, "alert_msg": ""},
        {"id": "t4", "name": "VIP 1", "zone": "VIP Loca", "status": "active", "x": 30, "y": 160, "w": 140, "h": 90, "notes": "VIP Rezervasyon: Ahmet Bey (1x Şarap)", "last_alert": None, "alert_msg": ""},
        {"id": "t5", "name": "Bahçe 1", "zone": "Bahçe", "status": "idle", "x": 30, "y": 280, "w": 85, "h": 85, "notes": "", "last_alert": None, "alert_msg": ""},
        {"id": "t6", "name": "Bahçe 2", "zone": "Bahçe", "status": "active", "x": 140, "y": 280, "w": 85, "h": 85, "notes": "3x Bira, 1x Patates", "last_alert": None, "alert_msg": ""},
        {"id": "t7", "name": "Bar Tezgahı 1", "zone": "Bar Tezgahı", "status": "active", "x": 200, "y": 160, "w": 160, "h": 65, "notes": "Bar misafiri: 2x Kokteyl", "last_alert": None, "alert_msg": ""}
    ]
}

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

config_data = load_config()

# WebSocket bağlantı yöneticisi
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for dc in dead_connections:
            self.disconnect(dc)

manager = ConnectionManager()

# Pydantic Modelleri
class TableCreate(BaseModel):
    name: str
    zone: str
    x: Optional[int] = 30
    y: Optional[int] = 40
    w: Optional[int] = 85
    h: Optional[int] = 85
    notes: Optional[str] = ""

class TableUpdate(BaseModel):
    name: Optional[str] = None
    zone: Optional[str] = None
    status: Optional[str] = None # 'idle', 'active', 'low', 'alert', 'serving'
    x: Optional[int] = None
    y: Optional[int] = None
    w: Optional[int] = None
    h: Optional[int] = None
    notes: Optional[str] = None

class ZoneCreate(BaseModel):
    name: str

class AlertTrigger(BaseModel):
    table_id: str
    alert_type: str = "empty_glass" # 'empty_glass', 'low_drink', 'call_waiter'
    message: str = "Kadeh Bitti! (2. Siparişi Sor)"

# --- API ENDPOINTS ---

@app.get("/api/state")
def get_state():
    """Tüm masa ve bölge durumunu döndürür"""
    return config_data

@app.post("/api/tables")
async def add_table(table: TableCreate):
    """Yeni masa ekler"""
    new_id = f"t_{int(datetime.now().timestamp() * 1000)}"
    new_table = {
        "id": new_id,
        "name": table.name,
        "zone": table.zone,
        "status": "idle",
        "x": table.x,
        "y": table.y,
        "w": table.w or 85,
        "h": table.h or 85,
        "notes": table.notes or "",
        "last_alert": None,
        "alert_msg": ""
    }
    config_data["tables"].append(new_table)
    save_config(config_data)
    await manager.broadcast({"type": "TABLES_UPDATED", "data": config_data})
    return new_table

@app.put("/api/tables/{table_id}")
async def update_table(table_id: str, payload: TableUpdate):
    """Masa adı, bölgesi, konumu, boyutu veya sipariş notunu günceller"""
    found = None
    for t in config_data["tables"]:
        if t["id"] == table_id:
            if payload.name is not None:
                t["name"] = payload.name
            if payload.zone is not None:
                t["zone"] = payload.zone
            if payload.status is not None:
                t["status"] = payload.status
                if payload.status != "alert":
                    t["alert_msg"] = ""
            if payload.x is not None:
                t["x"] = payload.x
            if payload.y is not None:
                t["y"] = payload.y
            if payload.w is not None:
                t["w"] = payload.w
            if payload.h is not None:
                t["h"] = payload.h
            if payload.notes is not None:
                t["notes"] = payload.notes
            found = t
            break

    if not found:
        raise HTTPException(status_code=404, detail="Masa bulunamadı")

    save_config(config_data)
    await manager.broadcast({"type": "TABLE_CHANGED", "table": found})
    return found

@app.delete("/api/tables/{table_id}")
async def delete_table(table_id: str):
    """Masayı siler"""
    config_data["tables"] = [t for t in config_data["tables"] if t["id"] != table_id]
    save_config(config_data)
    await manager.broadcast({"type": "TABLES_UPDATED", "data": config_data})
    return {"success": True}

@app.post("/api/zones")
async def add_zone(zone: ZoneCreate):
    """Yeni mekan bölgesi ekler (örn. Teras, Balkon vb.)"""
    if zone.name not in config_data["zones"]:
        config_data["zones"].append(zone.name)
        save_config(config_data)
        await manager.broadcast({"type": "TABLES_UPDATED", "data": config_data})
    return config_data["zones"]

@app.delete("/api/zones/{zone_name}")
async def delete_zone(zone_name: str):
    """Bölgeyi siler ve o bölgedeki masaları güvenle diğer bölgeye taşır"""
    if zone_name in config_data["zones"]:
        config_data["zones"].remove(zone_name)
        fallback_zone = config_data["zones"][0] if config_data["zones"] else "Genel"
        if fallback_zone == "Genel" and "Genel" not in config_data["zones"]:
            config_data["zones"].append("Genel")
        # O bölgedeki masaları aktar
        for t in config_data["tables"]:
            if t["zone"] == zone_name:
                t["zone"] = fallback_zone
        save_config(config_data)
        await manager.broadcast({"type": "TABLES_UPDATED", "data": config_data})
    return {"success": True}

@app.post("/api/alert")
async def trigger_alert(alert: AlertTrigger):
    """Kamera veya sensör tarafından tetiklenen ALARM bildirimi"""
    target = None
    for t in config_data["tables"]:
        if t["id"] == alert.table_id or t["name"].lower() == alert.table_id.lower():
            t["status"] = "alert"
            t["last_alert"] = datetime.now().strftime("%H:%M:%S")
            t["alert_msg"] = alert.message
            target = t
            break

    if not target:
        # Eğer masa yoksa otomatik oluştur
        new_id = f"t_{int(datetime.now().timestamp() * 1000)}"
        target = {
            "id": new_id,
            "name": alert.table_id,
            "zone": "Genel",
            "status": "alert",
            "x": 100,
            "y": 100,
            "last_alert": datetime.now().strftime("%H:%M:%S"),
            "alert_msg": alert.message
        }
        config_data["tables"].append(target)

    save_config(config_data)

    # Anlık bildirim fırlat
    event = {
        "type": "NEW_ALERT",
        "table": target,
        "message": alert.message,
        "time": target["last_alert"]
    }
    await manager.broadcast(event)
    return {"success": True, "table": target}

@app.post("/api/acknowledge/{table_id}")
async def acknowledge_alert(table_id: str):
    """Garson 'Masaya Gittim / Tamamlandı' butonuna bastığında çağrılır"""
    for t in config_data["tables"]:
        if t["id"] == table_id:
            t["status"] = "serving" # Garson ilgileniyor
            t["alert_msg"] = "Garson ilgileniyor"
            break
    save_config(config_data)
    await manager.broadcast({"type": "ALERT_ACKNOWLEDGED", "table_id": table_id, "data": config_data})
    return {"success": True}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # İlk bağlantıda tüm mevcut durumu gönder
    await websocket.send_json({"type": "INITIAL_STATE", "data": config_data})
    try:
        while True:
            # İstemciden gelen mesajları dinle
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                if parsed.get("action") == "ACKNOWLEDGE":
                    await acknowledge_alert(parsed.get("table_id"))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Statik web arayüzü sunumu
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8000
    print("\n" + "="*60)
    print(" 🍻 PUB & BAR OTOMASYONU - MERKEZI SUNUCU BASLATILDI")
    print("="*60)
    print(f" -> Bilgisayardan erisim : http://localhost:{port}")
    print(f" -> TELEFONDAN ERISIM   : http://{local_ip}:{port}")
    print("    (iPhone ve Android telefonunuzun tarayicisindan bu adrese girin)")
    print("="*60 + "\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
