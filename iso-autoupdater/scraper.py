import re
import requests
from bs4 import BeautifulSoup

def _get_soup(url):
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')

def get_ubuntu_latest(allow_betas=False):
    """
    Scrapes the Ubuntu releases page for the latest LTS or current release.
    """
    url = "https://releases.ubuntu.com/"
    soup = _get_soup(url)
    print("Downloading Ubuntu image")
    
    versions = []
    # Find all release directories like 24.04/ or 24.04-beta/
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and re.match(r'^\d{2}\.\d{2}(?:-[a-zA-Z0-9]+)?/$', href):
            if not allow_betas and ('beta' in href.lower() or 'rc' in href.lower()):
                continue
            versions.append(href.strip('/'))
            
    print(versions)

    if versions:
        # Sort and get the most recent version directory
        # This sorts versions using pure string sorting or split by dot/dash
        def sort_key(s):
            # Try to grab just the numbers for sorting '24.04-beta'
            base = s.split('-')[0]
            return [int(x) for x in base.split('.')]
        
        versions.sort(key=sort_key, reverse=True)
        tries = 0
        while tries < len(versions):
            latest_dir = versions[tries]
            sub_url = f"{url}{latest_dir}/"
            print(sub_url)
            
            try:
                sub_soup = _get_soup(sub_url)
                for link in sub_soup.find_all('a'):
                    sub_href = link.get('href')
                    if sub_href and sub_href.endswith('desktop-amd64.iso'):
                        filename = sub_href.split('/')[-1]
                        print(filename)
                        match = re.search(r'ubuntu-(.+)-desktop-amd64\.iso', filename)
                        print(match)
                        if match:
                            version = match.group(1)
                            if not allow_betas and ('beta' in version.lower() or 'rc' in version.lower()):
                                continue
                            full_url = sub_href if sub_href.startswith("http") else f"{sub_url}{sub_href.lstrip('/')}"
                            print(full_url)
                            return version, full_url
            except Exception as e:
                print(f"Error accessing ubuntu specific directory {sub_url}: {e}")
            tries += 1
                
    # Fallback to a hardcoded known release if scraping fails
    return "0.0.0", ""

def get_debian_latest(allow_betas=False):
    """
    Scrapes the Debian cdimage repository.
    """
    url = "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/"
    # For Debian betas usually they are in a completely different testing tree 
    # but we'll handle the parameter smoothly here in case 'rc' appears.
    try:
        soup = _get_soup(url)
    except Exception:
        return "0.0.0", ""
    
    for link in soup.find_all('a'):
        href = link.get('href')
        # Typical format: debian-12.8.0-amd64-netinst.iso
        if href and re.match(r'debian-\d+\.\d+\.\d+(?:-\w+)?-amd64-netinst\.iso', href):
            match = re.search(r'debian-([\d.]+(?:-\w+)?)-amd64-netinst\.iso', href)
            if match:
                version = match.group(1)
                if not allow_betas and ('beta' in version.lower() or 'rc' in version.lower()):
                    continue
                full_url = f"{url}{href}"
                return version, full_url
                
    return "0.0.0", ""

def get_arch_latest(allow_betas=False):
    """
    Scrapes the Arch Linux kernel mirrors directory.
    (Arch is a rolling release, rarely has traditional ISO betas, but logic stands)
    """
    url = "https://mirrors.kernel.org/archlinux/iso/latest/"
    try:
        soup = _get_soup(url)
    except Exception:
        return "0.0.0", ""
    
    for link in soup.find_all('a'):
        href = link.get('href')
        # Typical format: archlinux-2024.12.01-x86_64.iso
        if href and re.match(r'archlinux-\d{4}\.\d{2}\.\d{2}(?:-\w+)?-x86_64\.iso', href):
            match = re.search(r'archlinux-(.+)-x86_64\.iso', href)
            if match:
                version = match.group(1)
                if not allow_betas and ('beta' in version.lower() or 'rc' in version.lower()):
                    continue
                full_url = f"{url}{href}"
                return version, full_url
                
    return "0.0.0", ""

def get_fedora_latest(allow_betas=False):
    """
    Scrapes the Fedora kernel mirrors directory.
    Finds the latest version folder, then finds the Workstation Live ISO.
    """
    mirror_url = "https://mirrors.kernel.org/fedora/releases/"
    try:
        soup = _get_soup(mirror_url)
    except Exception:
        return "0.0.0", ""
    
    versions = []
    # Identify the greatest raw release number available (e.g., 40, 41)
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and re.match(r'^\d+(?:_beta|_rc)?/$', href.lower()):
            if not allow_betas and ('beta' in href.lower() or 'rc' in href.lower()):
                continue
            # Keep directories that are numbers
            dir_name = href.strip('/')
            versions.append(dir_name)
                
    if versions:
        # Sort properly handling strings and numbers
        def sort_key(s):
            nums = [int(n) for n in re.findall(r'\d+', s)]
            return nums[0] if nums else 0
        versions.sort(key=sort_key, reverse=True)
        latest = versions[0]
        
        iso_dir = f"{mirror_url}{latest}/Workstation/x86_64/iso/"
        try:
            iso_soup = _get_soup(iso_dir)
            for file_link in iso_soup.find_all('a'):
                href = file_link.get('href')
                if href and href.startswith('Fedora-Workstation') and href.endswith('.iso'):
                    match = re.search(r'Fedora-Workstation-(.+).iso', href)
                    if match:
                        version_full = match.group(1)
                        if not allow_betas and ('beta' in version_full.lower() or 'rc' in version_full.lower()):
                            continue
                        full_url = f"{iso_dir}{href}"
                        return version_full, full_url
        except Exception as e:
            print(f"Error accessing fedora specific iso directory: {e}")
            
    return "0.0.0", ""

def get_proxmox_latest(allow_betas=False):
    """
    Scrapes the Proxmox enterprise mirror for the latest VE ISO.
    """
    url = "https://enterprise.proxmox.com/iso/"
    try:
        soup = _get_soup(url)
    except Exception:
        return "0.0.0", ""
    
    versions = []
    for link in soup.find_all('a'):
        href = link.get('href')
        # Typical format: proxmox-ve_8.4-1.iso
        if href and re.match(r'proxmox-ve_[\w.-]+\.iso', href):
            match = re.search(r'proxmox-ve_([A-Za-z0-9.-]+)\.iso', href)
            if match:
                version = match.group(1)
                if not allow_betas and ('beta' in version.lower() or 'rc' in version.lower()):
                    continue
                versions.append((version, f"{url}{href}"))
                
    if versions:
        # Sort by version number
        def sort_key(item):
            nums = [int(n) for n in re.findall(r'\d+', item[0])]
            return nums
        versions.sort(key=sort_key, reverse=True)
        return versions[0][0], versions[0][1]
        
    return "0.0.0", ""

def get_kali_latest(allow_betas=False):
    """
    Scrapes the Kali Linux cdimage repository for the latest installer ISO.
    """
    url = "https://cdimage.kali.org/current/"
    try:
        soup = _get_soup(url)
    except Exception:
        return "0.0.0", ""
    
    for link in soup.find_all('a'):
        href = link.get('href')
        # Typical format: kali-linux-2026.1-installer-amd64.iso
        if href and re.match(r'kali-linux-[\w.-]+-installer-amd64\.iso', href):
            match = re.search(r'kali-linux-([A-Za-z0-9.-]+)-installer-amd64\.iso', href)
            if match:
                version = match.group(1)
                if not allow_betas and ('beta' in version.lower() or 'rc' in version.lower() or 'weekly' in version.lower()):
                    continue
                full_url = f"{url}{href}"
                return version, full_url
                
    return "0.0.0", ""

def get_latest_iso_info(distro_name, allow_betas=False):
    """
    Returns a tuple of (version, download_url) for the specified distro.
    None, None if failed.
    """
    try:
        if distro_name == "Ubuntu":
            return get_ubuntu_latest(allow_betas)
        if distro_name == "Debian":
            return get_debian_latest(allow_betas)
        if distro_name == "Arch":
            return get_arch_latest(allow_betas)
        if distro_name == "Fedora":
            return get_fedora_latest(allow_betas)
        if distro_name == "Proxmox":
            return get_proxmox_latest(allow_betas)
        if distro_name == "Kali":
            return get_kali_latest(allow_betas)
            
    except Exception as e:
        print(f"Error fetching {distro_name} ISO information: {e}")
        
    return None, None
