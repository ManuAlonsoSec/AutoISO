import os
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from scraper import get_latest_iso_info

class DownloadThread(QThread):
    progress_updated = pyqtSignal(str, int)  # distro, percentage
    status_updated = pyqtSignal(str, str)    # distro, status message
    finished_task = pyqtSignal(str)          # distro emitted when specific task concludes
    
    def __init__(self, distros_to_check, download_dir, download_betas=False):
        super().__init__()
        self.distros_to_check = distros_to_check
        self.download_dir = Path(download_dir)
        self.download_betas = download_betas
        self.is_cancelled = False

    def run(self):
        """
        Executes the checking and downloading in the background.
        """
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        for distro in self.distros_to_check:
            if self.is_cancelled:
                self.status_updated.emit(distro, "Cancelled")
                break
                
            self.status_updated.emit(distro, "Checking latest version...")
            version, url = get_latest_iso_info(distro, self.download_betas)
            
            if not version or not url or version == "0.0.0":
                self.status_updated.emit(distro, "Failed to fetch version")
                self.finished_task.emit(distro)
                continue

            iso_filename = url.split('/')[-1]
            target_path = self.download_dir / iso_filename

            # Check if this exact file is already present
            if target_path.exists():
                self.status_updated.emit(distro, f"Up to date (v{version})")
                self.progress_updated.emit(distro, 100)
                self.finished_task.emit(distro)
                continue

            self.status_updated.emit(distro, f"Downloading v{version}...")
            
            try:
                # Streaming the file download
                response = requests.get(url, stream=True, timeout=15)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                downloaded_size = 0
                temp_target_path = target_path.with_suffix('.iso.part')

                with open(temp_target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.is_cancelled:
                            break
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                percent = int((downloaded_size / total_size) * 100)
                                self.progress_updated.emit(distro, percent)

                if self.is_cancelled:
                    if temp_target_path.exists():
                        temp_target_path.unlink()
                    self.status_updated.emit(distro, "Cancelled")
                    continue

                # Finalize the download
                if temp_target_path.exists():
                    temp_target_path.rename(target_path)

                # Delete old versions
                self._delete_old_versions(distro, iso_filename)

                self.progress_updated.emit(distro, 100)
                self.status_updated.emit(distro, f"Updated to v{version}")
                
            except requests.exceptions.RequestException as e:
                self.status_updated.emit(distro, "Connection Error")
                print(f"Request exception for {distro} at {url}: {e}")
            except Exception as e:
                self.status_updated.emit(distro, "File Error")
                print(f"File exception for {distro}: {e}")
                
            self.finished_task.emit(distro)

    def cancel(self):
        """
        Gracefully cancels the running background tasks.
        """
        self.is_cancelled = True

    def _delete_old_versions(self, distro_name, current_filename):
        """
        Delete old ISO files belonging to the same distribution.
        """
        prefix = distro_name.lower()
        if prefix == "arch":
            prefix = "archlinux"
            
        for file in self.download_dir.glob("*.iso"):
            if file.name == current_filename:
                continue
                
            # Naive match purely by generic prefix conventions
            if file.name.lower().startswith(prefix):
                try:
                    file.unlink()
                    print(f"Auto-deleted old version: {file.name}")
                except Exception as e:
                    print(f"Failed to auto-delete {file.name}: {e}")
