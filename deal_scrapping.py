import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import sys
import itertools
from typing import Optional
import threading


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


def scrape_hbl_deals(url):
    """
    Scrape deals information from HBL website and store in CSV
    """
    progress = ProgressIndicator("Connecting to website")
    progress.start()

    try:
        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Make HTTP request
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        progress.stop()
        print("\nWebsite connected successfully!")

        # Update progress message for parsing
        progress = ProgressIndicator("Parsing webpage content")
        progress.start()

        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Initialize list to store deals
        deals = []

        # Find all deal containers (you'll need to update these selectors based on actual HTML structure)
        deal_containers = soup.find_all('div', class_='card-body')  # Updated selector

        progress.stop()

        if not deal_containers:
            print("\nNo deal containers found. Debug information:")
            print(f"Status Code: {response.status_code}")
            print("First 500 characters of HTML:")
            print(response.text[:500])
            return None

        print(f"\nFound {len(deal_containers)} potential deals. Processing...")

        # New progress indicator for processing deals
        progress = ProgressIndicator("Extracting deal information")
        progress.start()

        for container in deal_containers:
            try:
                deal = {
                    'merchant_name': container.find('h2', class_='title').text.strip() if container.find('h2',
                                                                                                         class_='title') else "N/A",
                    'discount': container.find('div', class_='discount').text.strip() if container.find('div',
                                                                                                        class_='discount') else "N/A",
                    'category': container.find('span', class_='category').text.strip() if container.find('span',
                                                                                                         class_='category') else "N/A",
                    'valid_until': container.find('div', class_='validity').text.strip() if container.find('div',
                                                                                                           class_='validity') else "N/A",
                    'description': container.find('p', class_='description').text.strip() if container.find('p',
                                                                                                            class_='description') else "N/A",
                    'location': container.find('div', class_='location').text.strip() if container.find('div',
                                                                                                        class_='location') else "N/A"
                }
                deals.append(deal)
            except AttributeError as e:
                print(f"\nError parsing deal container: {e}")
                continue

        progress.stop()
        print(f"\nSuccessfully processed {len(deals)} deals")

        return deals

    except requests.RequestException as e:
        progress.stop()
        print(f"\nError fetching the webpage: {e}")
        return None
    except Exception as e:
        progress.stop()
        print(f"\nUnexpected error: {e}")
        return None


def save_to_csv(deals, filename=None):
    """
    Save scraped deals to CSV file
    """
    if not deals:
        print("No deals to save")
        return

    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'hbl_deals_{timestamp}.csv'

    progress = ProgressIndicator("Saving to CSV")
    progress.start()

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = deals[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(deals)

        progress.stop()
        print(f"\nSuccessfully saved {len(deals)} deals to {filename}")

    except IOError as e:
        progress.stop()
        print(f"\nError saving to CSV: {e}")


def main():
    url = "https://hbl-web.peekaboo.guru/karachi/places/_all/all"
    print("Starting scraping process...")
    print("=" * 50)

    # Add delay to be respectful to the server
    time.sleep(1)

    deals = scrape_hbl_deals(url)
    if deals:
        save_to_csv(deals)

    print("=" * 50)
    print("Scraping process completed!")


if __name__ == "__main__":
    main()