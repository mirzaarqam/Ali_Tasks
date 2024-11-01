import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import sys
import itertools
import threading
from typing import Optional


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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        progress.stop()
        print("\nWebsite connected successfully!")

        # Save HTML to a file for debugging purposes
        with open("hbl_deals_page.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        print("HTML content saved to hbl_deals_page.html")

        # Parsing progress
        progress = ProgressIndicator("Parsing webpage content")
        progress.start()

        soup = BeautifulSoup(response.content, 'html.parser')

        deals = []

        # Locate product name and discount percentage using the identified classes
        product_elements = soup.find_all('p', class_='Styled__CardHeaderTitle-ii87o4-9 bUUkkc')
        discount_elements = soup.find_all('div', class_='Styled__Holder-jw4r3n-0 bfuynF')

        progress.stop()

        if not product_elements or not discount_elements:
            print("\nNo product or discount information found.")
            return None

        print(f"\nFound {len(product_elements)} products. Processing...")

        progress = ProgressIndicator("Extracting deal information")
        progress.start()

        # Zip the two lists to get products with corresponding discounts
        for product, discount in zip(product_elements, discount_elements):
            try:
                product_name = product.text.strip() if product else "N/A"
                discount_text = discount.get_text(separator=" ").strip() if discount else "N/A"

                deal = {
                    'product': product_name,
                    'discount': discount_text
                }
                deals.append(deal)
            except AttributeError as e:
                print(f"\nError parsing deal: {e}")
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

    time.sleep(1)

    deals = scrape_hbl_deals(url)
    if deals:
        save_to_csv(deals)

    print("=" * 50)
    print("Scraping process completed!")


if __name__ == "__main__":
    main()
