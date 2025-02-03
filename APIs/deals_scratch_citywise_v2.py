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


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def each_deal_details(url, city):
    print(f"City is: {city}")

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.binary_location = conf.CHROMIUM_BINARIES
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # Initialize WebDriver
    service = Service(executable_path=conf.CHROME_DRIVERS)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Load initial page and expand all items
        print("Loading initial page and expanding all deals...")
        driver.get(url)

        # Click all "See More" buttons
        while True:
            try:
                see_more = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//p[contains(@class, 'FlatButton__Text-sc-952pz8-1') and contains(., 'See More')]")
                    )
                )
                driver.execute_script("arguments[0].scrollIntoView();", see_more)
                see_more.click()
                time.sleep(2)  # Allow time for new items to load
            except Exception as e:
                print("All deals expanded or no more 'See More' buttons")
                break

        # Get all city blocks after full expansion
        city_blocks = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[contains(@class, 'Styled__CardHolder-ii87o4-1')]")
            )
        )
        print(f"Total deals found: {len(city_blocks)}")

        deals = {}

        # Process each deal in new tab
        for index in tqdm(range(len(city_blocks)), desc="Processing Deals"):
            try:
                # Re-fetch blocks to avoid staleness
                city_blocks = driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'Styled__CardHolder-ii87o4-1')]"
                )

                if index >= len(city_blocks):
                    print(f"Stopped at index {index} - elements changed")
                    break

                # Get deal URL using JavaScript to avoid detachment
                deal_url = driver.execute_script(
                    "return arguments[0].querySelector('a').href;",
                    city_blocks[index]
                )

                # Open new tab
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[1])

                # Load deal page
                driver.get(deal_url)
                time.sleep(3)  # Allow page to load

                # Extract deal details
                try:
                    deal_name = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//h1[contains(@class, 'Styled__EntityTitle-sc-1h7b0kv-4')]")
                        )
                    ).text.strip()
                except:
                    deal_name = "N/A"

                # Process discounts
                discount_entries = []
                discount_elements = driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'Styled__ListTextArea-sc-14n6kj-6')]"
                )

                for element in discount_elements:
                    try:
                        discount = element.find_element(
                            By.XPATH, ".//div[contains(@class, 'Styled__PrimaryText-sc-14n6kj-7')]"
                        ).text.strip()

                        # Get card types
                        cards = set()
                        card_elements = element.find_elements(
                            By.XPATH, ".//div[contains(@class, 'Style__CardButton-s2xhwj-3')]"
                        )
                        for card in card_elements:
                            try:
                                card_text = card.find_element(By.TAG_NAME, "p").text.strip()
                                cards.add(card_text)
                            except:
                                try:
                                    card_text = card.find_element(By.TAG_NAME, "span").text.strip()
                                    cards.add(card_text)
                                except:
                                    pass

                        if discount and cards:
                            discount_entries.append({
                                "discount": discount,
                                "cards": list(cards)
                            })
                    except Exception as e:
                        print(f"Error processing discount: {str(e)}")
                        continue

                # Store collected data
                if deal_name and discount_entries:
                    deals[deal_name] = discount_entries

                # Close current tab and return to main
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)  # Brief pause for tab switch

            except Exception as e:
                print(f"Error processing deal {index}: {str(e)}")
                # Ensure we return to main tab
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

        # Save results to CSV
        output_folder = "DataManager"
        os.makedirs(output_folder, exist_ok=True)
        csv_path = os.path.join(output_folder, f"{city}_deals.csv")

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["City", "Deal Name", "Discount", "Applicable Cards"])

            for deal_name, entries in deals.items():
                for entry in entries:
                    writer.writerow([
                        city,
                        deal_name,
                        entry["discount"],
                        ", ".join(entry["cards"])
                    ])

        print(f"Successfully saved {len(deals)} deals to {csv_path}")

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
    cities = ["islamabad", "rawalpindi", "multan", "peshawar", "faisalabad", "lahore"]
    for city in cities:
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
