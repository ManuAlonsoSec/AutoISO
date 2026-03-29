import json
import os
import winreg
from pathlib import Path

CONFIG_FILE = "settings.json"

class ConfigManager:
    def __init__(self):
        self.config = {
            "download_dir": str(Path.home() / "Downloads" / "ISOs"),
            "run_at_startup": False,
            "download_betas": False,
            "distros": {
                "Ubuntu": True,
                "Debian": True,
                "Fedora": True,
                "Arch": True,
                "Proxmox": False,
                "Kali": False
            }
        }
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    
                    # Carefully merge the dicts to prevent overriding with partial data
                    for key, value in loaded_config.items():
                        if isinstance(value, dict) and isinstance(self.config.get(key), dict):
                            self.config[key].update(value)
                        else:
                            self.config[key] = value
            except Exception as e:
                print(f"Error loading {CONFIG_FILE}: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving {CONFIG_FILE}: {e}")

    def get(self, key):
        return self.config.get(key)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def set_startup(self, enable):
        self.set("run_at_startup", enable)
        
        # Windows Registry logic for Startup
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_WRITE
            )
            app_name = "ISOAutoupdate"
            app_path = os.path.abspath("main.py")
            
            import sys
            # Assuming typical Python setup where pythonw.exe should run UI without console
            python_exe = sys.executable.replace("python.exe", "pythonw.exe")
            command = f'"{python_exe}" "{app_path}" --startup'
            
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass # Key didn't exist anyway
            winreg.CloseKey(key)
            print(f"Registry startup set to {enable}")
        except Exception as e:
            print(f"Failed to modify Windows Registry for startup: {e}")
