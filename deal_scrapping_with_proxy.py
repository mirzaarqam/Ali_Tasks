import os

import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import sys
import itertools
import threading
from typing import Optional
import winreg
import urllib.parse
import socket


class ProgressIndicator:
    def __init__(self, description: str = "Processing"):
        self.description = description
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def _animate(self):
        for c in itertools.cycle(['⢿', '⣻', '⣽', '⣾', '⣷', '⣯', '⣟', '⡿']):
            if not self.is_running:
                break
            sys.stdout.write(f'\r{self.description} {c}')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r')

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._animate)
        self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread is not None:
            self._thread.join()


def get_windows_proxy_settings():
    """Get Windows proxy settings from registry"""
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        registry_key = winreg.OpenKey(registry, r'Software\Microsoft\Windows\CurrentVersion\Internet Settings')
        proxy_enable = winreg.QueryValueEx(registry_key, 'ProxyEnable')[0]

        if proxy_enable:
            proxy_server = winreg.QueryValueEx(registry_key, 'ProxyServer')[0]
            return proxy_server
        return None
    except Exception as e:
        print(f"Error reading Windows proxy settings: {e}")
        return None


def get_proxy_settings():
    """Get proxy settings from multiple sources"""
    print("\nDetecting proxy settings...")

    # Try environment variables first
    env_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    if env_proxy:
        print("Found proxy settings in environment variables")
        return {'http': env_proxy, 'https': env_proxy}

    # Try Windows registry
    windows_proxy = get_windows_proxy_settings()
    if windows_proxy:
        if not windows_proxy.startswith('http'):
            windows_proxy = f'http://{windows_proxy}'
        print("Found proxy settings in Windows registry")
        return {'http': windows_proxy, 'https': windows_proxy}

    # Manual configuration
    print("No proxy settings found automatically.")
    use_proxy = input("Do you want to enter proxy settings manually? (y/n): ").lower() == 'y'

    if use_proxy:
        proxy_host = input("Enter proxy host (e.g., proxy.company.com): ")
        proxy_port = input("Enter proxy port (e.g., 8080): ")
        use_auth = input("Does your proxy require authentication? (y/n): ").lower() == 'y'

        if use_auth:
            proxy_user = input("Enter proxy username: ")
            proxy_pass = input("Enter proxy password: ")
            proxy_string = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        else:
            proxy_string = f"http://{proxy_host}:{proxy_port}"

        return {'http': proxy_string, 'https': proxy_string}

    return None


def create_session():
    """Create a requests session with proxy settings"""
    session = requests.Session()

    # Get proxy settings
    proxies = get_proxy_settings()
    if proxies:
        session.proxies = proxies
        print(f"Using proxy settings: {proxies}")

    # Set headers
    session.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    # Configure session
    session.verify = False  # Sometimes needed for corporate proxies
    requests.packages.urllib3.disable_warnings()  # Disable SSL warnings

    # Test connection
    try:
        print("\nTesting connection...")
        test_url = 'http://www.google.com'  # More reliable test URL
        response = session.get(test_url, timeout=30)
        print(f"Connection test successful! Status code: {response.status_code}")
        return session
    except requests.exceptions.RequestException as e:
        print(f"\nConnection test failed: {e}")
        retry = input("Continue anyway? (y/n): ").lower() == 'y'
        if not retry:
            sys.exit(1)
        return session


def scrape_hbl_deals(url, session):
    """Scrape deals information from HBL website"""
    progress = ProgressIndicator("Connecting to website")
    progress.start()

    try:
        # Try to resolve domain first
        domain = urllib.parse.urlparse(url).netloc
        print(f"\nResolving domain {domain}...")
        ip = socket.gethostbyname(domain)
        print(f"Domain resolved to IP: {ip}")

        # Make request with extended timeout and retries
        response = session.get(
            url,
            timeout=60,
            allow_redirects=True,
            verify=False
        )

        progress.stop()

        # Check response
        if response.status_code != 200:
            print(f"\nUnexpected status code: {response.status_code}")
            print("Response headers:", dict(response.headers))
            return None

        print("\nWebsite connected successfully!")

        # Save raw HTML for debugging
        with open('raw_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("Saved raw HTML to 'raw_response.html'")

        # Parse content
        soup = BeautifulSoup(response.content, 'html.parser')
        deals = []

        # Find deal containers
        deal_containers = soup.find_all('div', class_='card-body')

        if not deal_containers:
            print("\nNo deal containers found. Trying alternative selectors...")
            # Try alternative selectors
            deal_containers = soup.find_all('div', class_=['deal', 'offer', 'promotion'])

        if deal_containers:
            for container in deal_containers:
                try:
                    deal = {
                        'merchant_name': container.find(['h2', 'h3', 'h4'],
                                                        class_=['title', 'merchant']).text.strip() if container.find(
                            ['h2', 'h3', 'h4']) else "N/A",
                        'discount': container.find(class_=['discount', 'offer-value']).text.strip() if container.find(
                            class_=['discount', 'offer-value']) else "N/A",
                        'description': container.find(['p', 'div'],
                                                      class_=['description', 'details']).text.strip() if container.find(
                            ['p', 'div'], class_=['description', 'details']) else "N/A",
                    }
                    deals.append(deal)
                except Exception as e:
                    print(f"Error parsing deal: {e}")
                    continue

            return deals
        else:
            print("\nNo deals found. Please check the HTML structure in 'raw_response.html'")
            return None

    except Exception as e:
        progress.stop()
        print(f"\nError: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if you can access the website in your browser")
        print("2. Verify proxy settings in Internet Explorer/Windows Settings")
        print("3. Try using a VPN if available")
        print("4. Check with your IT department about any specific proxy requirements")
        return None


def save_to_csv(deals, filename=None):
    """Save deals to CSV file"""
    if not deals:
        print("No deals to save")
        return

    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'hbl_deals_{timestamp}.csv'

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=deals[0].keys())
            writer.writeheader()
            writer.writerows(deals)
        print(f"\nSaved {len(deals)} deals to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")


def main():
    url = "https://www.hbl.com/personal/cards/hbl-deals-and-discounts"
    print("Starting scraping process...")
    print("=" * 50)

    session = create_session()
    deals = scrape_hbl_deals(url, session)

    if deals:
        save_to_csv(deals)

    print("=" * 50)
    print("Process completed!")


if __name__ == "__main__":
    main()