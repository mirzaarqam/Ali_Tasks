import csv
import time
from datetime import datetime
from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from progress_indicator import ProgressIndicator

app = Flask(__name__)


def scrape_hbl_deals(url, city):
    """
    Scrape deals information from HBL website for a specific city.
    """
    # Set up Selenium with Chrome in headless mode
    chrome_options = Options()
    chrome_options.binary_location = "/snap/bin/chromium"  # Replace with your actual Chromium path
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    service = Service(executable_path="/home/arqam/Downloads/chromedriver-linux64/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Start progress indicator
    progress = ProgressIndicator("Connecting to website")
    progress.start()

    try:
        driver.get(url)
        time.sleep(5)  # Wait for the page to load completely

        progress.stop()
        print("\nWebsite connected and loaded successfully!")

        deals = []
        collected_product_names = set()  # To track already collected product names

        while True:
            # Check for the "See More" button
            see_more_button = driver.find_elements(By.XPATH,
                                                   "//p[contains(@class, 'FlatButton__Text-sc-952pz8-1') and contains(., 'See More')]")
            if see_more_button:
                see_more_button[0].click()  # Click the first "See More" button
                time.sleep(5)  # Wait for new items to load
            else:
                print("\nNo more items to load.")
                break

        # Save page source for debugging purposes
        page_source = driver.page_source

        # Parsing the rendered page with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Locate product name and discount percentage using identified classes
        product_elements = soup.find_all('p', class_='Styled__CardHeaderTitle-ii87o4-9 bUUkkc')
        discount_elements = soup.find_all('div', class_='Styled__Holder-jw4r3n-0 bfuynF')

        if not product_elements or not discount_elements:
            print("\nNo product or discount information found.")

        print(f"\nFound {len(product_elements)} products on this page. Processing...")

        progress = ProgressIndicator("Extracting deal information")
        progress.start()

        # Zip the two lists to get products with corresponding discounts
        for product, discount in zip(product_elements, discount_elements):
            product_name = product.text.strip() if product else "N/A"
            discount_text = discount.get_text(separator=" ").strip() if discount else "N/A"

            # Only add new products that haven't been collected before
            if product_name not in collected_product_names:
                deals.append({
                    'city': city,  # Add city name to each entry
                    'product': product_name,
                    'discount': discount_text
                })
                collected_product_names.add(product_name)  # Track collected product names

        progress.stop()
        print(f"\nSuccessfully processed {len(deals)} deals in total")

        driver.quit()  # Close the browser session
        return deals

    except Exception as e:
        progress.stop()
        print(f"\nError: {e}")
        driver.quit()
        return None


def save_to_csv(deals, filename=None):
    """
    Save scraped deals to CSV file.
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
            # Get the field names from the first deal, excluding 'city' since it's already in the keys
            fieldnames = ['city'] + [key for key in deals[0].keys() if key != 'city']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(deals)

        progress.stop()
        print(f"\nSuccessfully saved {len(deals)} deals to {filename}")

    except IOError as e:
        progress.stop()
        print(f"\nError saving to CSV: {e}")


@app.route('/api/scrape_deals', methods=['GET'])
def api_scrape_deals():
    city = request.args.get('city', default="karachi", type=str)
    url = f"https://hbl-web.peekaboo.guru/{city}/places/_all/all"
    print(f"Starting scraping process for city: {city}")

    # Scrape the deals
    deals = scrape_hbl_deals(url, city)

    if deals:
        # Save deals to CSV
        save_to_csv(deals)

        # Return deals as JSON
        return jsonify(deals)
    else:
        return jsonify({"error": "Failed to scrape deals"}), 500


if __name__ == "__main__":
    app.run(debug=True)
