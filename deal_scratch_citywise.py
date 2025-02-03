import csv
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from Configs.progress_indicator import ProgressIndicator
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from Configs import configs as conf
def scrape_hbl_deals(url, city):
    """
    Scrape deals information from HBL website and store in CSV
    """
    # Set up Selenium with Chrome in headless mode
    chrome_options = Options()
    chrome_options.binary_location = conf.CHROMIUM_BINARIES  # Replace with your actual Chromium path
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    service = Service(executable_path=conf.CHROME_DRIVERS)
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


def each_deal_details(url, city):
    print(f"City is: {city}")
    chrome_options = Options()
    chrome_options.binary_location = conf.CHROMIUM_BINARIES  # Replace with your actual Chromium path
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    service = Service(executable_path=conf.CHROME_DRIVERS)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Start progress indicator
    progress = ProgressIndicator("Connecting to website")
    progress.start()

    try:
        driver.get(url)
        time.sleep(5)  # Wait for the page to load completely

        progress.stop()
        print("\nWebsite connected and loaded successfully!")

        deals = {}

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

        deals_block = driver.find_elements(By.XPATH, "//div[contains(@class, 'Styled__CardHolder-ii87o4-1')]")
        print(len(deals_block))

        for i in range(len(deals_block)):
            # Re-fetch city blocks to avoid stale element issues
            print(i)
            city_blocks = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, 'Styled__CardHolder-ii87o4-1')]"))
            )
            # Ensure `i` is within the bounds of `city_blocks`
            if i >= len(city_blocks):
                print(f"Index {i} out of range for city blocks.")
                break

            # Click the city block and retrieve the resulting URL
            city_blocks[i].click()
            time.sleep(5)  # Allow time for the new content to load

            # Extract deal name
            deal_name = driver.find_element(By.XPATH, "//h1[contains(@class, 'Styled__EntityTitle-sc-1h7b0kv-4 lnQoDw')]").text

            # Collect discount and card type details
            discount_elements = driver.find_elements(By.XPATH,
                                                     "//div[contains(@class, 'Styled__ListTextArea-sc-14n6kj-6')]")
            # for discount_element in discount_elements:

            for discount_element in tqdm(discount_elements, desc="Processing Discounts"):
                # Extract discount
                discount_text = discount_element.find_element(By.XPATH,
                                                              ".//div[contains(@class, 'Styled__PrimaryText-sc-14n6kj-7')]").text

                # Extract card types, checking for both <p> and <span> tags
                card_buttons = discount_element.find_elements(By.XPATH,
                                                              ".//div[contains(@class, 'Style__CardButton-s2xhwj-3')]")
                card_types = set()  # Use a set to avoid duplicates
                for button in card_buttons:
                    try:
                        # Attempt to retrieve text from <p> for card names
                        card_type = button.find_element(By.TAG_NAME, "p").text
                        card_types.add(card_type)
                    except:
                        # If <p> is not found, fallback to <span> for "+ N More Cards"
                        card_type = button.find_element(By.TAG_NAME, "span").text
                        card_types.add(card_type)

                # Only save deals with applicable cards
                if card_types:
                    # Add or update the deal entry in the deals dictionary
                    if deal_name not in deals:
                        deals[deal_name] = []

                    # Add this specific discount entry
                    deals[deal_name].append({
                        "discount": discount_text,
                        "cards": list(card_types)
                    })

            # Return to the main page to refresh city blocks for the next iteration
            driver.get(url)
            time.sleep(5)

        # Print all consolidated deals
        for deal_name, deal_info in deals.items():
            print(f"\nDeal Name: {deal_name}")
            for entry in deal_info:
                print(f"  Discount: {entry['discount']}")
                print(f"  Applicable Cards: {', '.join(entry['cards'])}")

        output_folder = "DataManager"
        csv_file_path = os.path.join(output_folder, f"{city}_deals.csv")
        with open(csv_file_path, "w", newline='', encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write header
            csv_writer.writerow(["City Name", "Deal Name", "Discount", "Applicable Cards"])

            # Write deal data
            for deal_name, deal_info in deals.items():
                for entry in deal_info:
                    csv_writer.writerow([
                        city,
                        deal_name,
                        entry["discount"],
                        ", ".join(entry["cards"])
                    ])

        print(f"\nData saved to {csv_file_path}")

    except Exception as e:
        print(e)
    finally:
        driver.quit()

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


def main():
    city = "karachi"
    url = f"https://hbl-web.peekaboo.guru/{city}/places/_all/all"
    print("Starting scraping process...")
    print("=" * 50)

    # deals = scrape_hbl_deals(url, city)
    deals = each_deal_details(url, city)# Pass city name to the scraping function
    # if deals:
    #     save_to_csv(deals)

    print("=" * 50)
    print("Scraping process completed!")


if __name__ == "__main__":
    main()
