import json
import os
import sys
import platform
from pathlib import Path

def _get_config_path():
    system = platform.system()
    app_name = "ISOAutoupdater"
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux / BSD
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_dir = base / app_name
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"

CONFIG_FILE = str(_get_config_path())

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
        
        system = platform.system()
        app_name = "ISOAutoupdater"
        
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            app_path = sys.executable
        else:
            app_path = os.path.abspath("main.py")
        
        try:
            if system == "Windows":
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE | winreg.KEY_WRITE
                )
                
                if is_frozen:
                    command = f'"{app_path}" --startup'
                else:
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
                print(f"Windows Registry startup set to {enable}")
                
            elif system == "Linux":
                autostart_dir = Path.home() / ".config" / "autostart"
                autostart_dir.mkdir(parents=True, exist_ok=True)
                desktop_file = autostart_dir / f"{app_name}.desktop"
                
                exec_cmd = f'"{app_path}" --startup' if is_frozen else f'{sys.executable} "{app_path}" --startup'
                
                if enable:
                    desktop_content = f"""[Desktop Entry]
Type=Application
Exec={exec_cmd}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=ISO Autoupdater
Comment=Automatically check and download ISO updates on startup
"""
                    desktop_file.write_text(desktop_content)
                else:
                    if desktop_file.exists():
                        desktop_file.unlink()
                print(f"Linux autostart set to {enable}")
                
            elif system == "Darwin":
                plist_dir = Path.home() / "Library" / "LaunchAgents"
                plist_dir.mkdir(parents=True, exist_ok=True)
                plist_file = plist_dir / f"com.{app_name.lower()}.startup.plist"
                
                if is_frozen:
                    args_xml = f"""        <string>{app_path}</string>
        <string>--startup</string>"""
                else:
                    args_xml = f"""        <string>{sys.executable}</string>
        <string>{app_path}</string>
        <string>--startup</string>"""
                
                if enable:
                    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{app_name.lower()}.startup</string>
    <key>ProgramArguments</key>
    <array>
{args_xml}
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
                    plist_file.write_text(plist_content)
                else:
                    if plist_file.exists():
                        plist_file.unlink()
                print(f"macOS LaunchAgent startup set to {enable}")
            else:
                print(f"Unsupported OS for startup configuration: {system}")
                
        except Exception as e:
            print(f"Failed to configure startup for {system}: {e}")
