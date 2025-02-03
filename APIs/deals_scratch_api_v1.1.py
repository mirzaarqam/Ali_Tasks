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
from flask import Flask, jsonify, request

app = Flask(__name__)

def each_deal_details(url, city):
    """
    Scrape deals from the specified URL for a given city and return structured data.
    """
    print(f"City is: {city}")
    chrome_options = Options()
    chrome_options.binary_location = conf.CHROMIUM_BINARIES
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
        time.sleep(5)

        progress.stop()
        print("\nWebsite connected and loaded successfully!")

        deals = {}

        while True:
            see_more_button = driver.find_elements(By.XPATH,
                                                   "//p[contains(@class, 'FlatButton__Text-sc-952pz8-1') and contains(., 'See More')]")
            if see_more_button:
                see_more_button[0].click()
                time.sleep(5)
            else:
                print("\nNo more items to load.")
                break

        deals_block = driver.find_elements(By.XPATH, "//div[contains(@class, 'Styled__CardHolder-ii87o4-1')]")

        for i in range(len(deals_block)):
            city_blocks = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, 'Styled__CardHolder-ii87o4-1')]"))
            )
            if i >= len(city_blocks):
                print(f"Index {i} out of range for city blocks.")
                break

            city_blocks[i].click()
            time.sleep(5)

            deal_name = driver.find_element(By.XPATH, "//h1[contains(@class, 'Styled__EntityTitle-sc-1h7b0kv-4 lnQoDw')]").text

            discount_elements = driver.find_elements(By.XPATH,
                                                     "//div[contains(@class, 'Styled__ListTextArea-sc-14n6kj-6')]")
            for discount_element in tqdm(discount_elements, desc="Processing Discounts"):
                discount_text = discount_element.find_element(By.XPATH,
                                                              ".//div[contains(@class, 'Styled__PrimaryText-sc-14n6kj-7')]").text

                card_buttons = discount_element.find_elements(By.XPATH,
                                                              ".//div[contains(@class, 'Style__CardButton-s2xhwj-3')]")
                card_types = set()
                for button in card_buttons:
                    try:
                        card_type = button.find_element(By.TAG_NAME, "p").text
                        card_types.add(card_type)
                    except:
                        card_type = button.find_element(By.TAG_NAME, "span").text
                        card_types.add(card_type)

                if card_types:
                    if deal_name not in deals:
                        deals[deal_name] = []
                    deals[deal_name].append({
                        "discount": discount_text,
                        "cards": list(card_types)
                    })

            driver.get(url)
            time.sleep(5)

        return deals  # Return data instead of saving to CSV

    except Exception as e:
        print(e)
        return None
    finally:
        driver.quit()

@app.route('/scrape_deals', methods=['GET'])
def scrape_deals():
    city = request.args.get('city', default="karachi", type=str)
    url = f"https://hbl-web.peekaboo.guru/{city}/places/_all/all"
    print("Starting scraping process...")
    print("=" * 50)

    deals = each_deal_details(url, city)  # Pass city name to the scraping function

    if deals is not None:
        response_data = {
            "city": city,
            "deals": deals
        }
        return jsonify(response_data)
    else:
        return jsonify({"error": "Failed to retrieve deals"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
