import csv
import time
import sys
import itertools
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Optional
from progress_indicator import ProgressIndicator



def extract_city_links(url):
    """
    Extract city links from HBL website and display in console
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

        progress.stop()
        print("\nWebsite connected and loaded successfully!")

        # Extracting city links
        progress = ProgressIndicator("Extracting Main City links")
        progress.start()

        city_links = []

        driver.get(url)
        time.sleep(5)  # Wait for the page to load completely

        progress.stop()
        print("\nWebsite connected and loaded successfully! above")
        city_blocks = driver.find_elements(By.XPATH,"//div[contains(@class, 'Styled__CityBlockHolder-m8ru5e-4')]")
        print(len(city_blocks))
        for i in range(len(city_blocks)):
            # Re-fetch city blocks to avoid stale element issues
            city_blocks = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, 'Styled__CityBlockHolder-m8ru5e-4')]"))
            )

            try:
                # Locate the <h3> and <h4> tags within each city block
                h3_text = city_blocks[i].find_element(By.TAG_NAME, 'h3').text

                # print(f"City Block {i + 1} - Location: {h3_text}")
            except Exception as e:
                print(f"Error retrieving text for city block {i + 1}: {e}")
                continue  # Skip to the next block if there's an issue

            # Click the city block and retrieve the resulting URL
            city_blocks[i].click()
            time.sleep(5)  # Allow time for the new content to load

            # Get and print the current URL after the click
            current_url = driver.current_url
            # print(f"URL after clicking: {current_url}")
            city_links.append((h3_text, current_url))

            # Return to the main page to refresh city blocks for the next iteration
            driver.get(url)
            time.sleep(5)

        progress = ProgressIndicator("Extracting Small City links")
        progress.start()



        driver.get(url)
        time.sleep(5)  # Wait for the page to load completely

        progress.stop()
        print("\nWebsite connected and loaded successfully! above")
        city_blocks = driver.find_elements(By.XPATH, "//div[contains(@class, 'Styled__CityTitle-m8ru5e-11')]")
        print(len(city_blocks))
        for i in range(len(city_blocks)):
            # Re-fetch city blocks to avoid stale element issues
            city_blocks = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class, 'Styled__CityTitle-m8ru5e-11')]"))
            )

            try:
                h3_text = city_blocks[i].text

                # print(f"City Block {i + 1} - Location: {h3_text}")
            except Exception as e:
                print(f"Error retrieving text for city block {i + 1}: {e}")
                continue  # Skip to the next block if there's an issue

            # Click the city block and retrieve the resulting URL
            city_blocks[i].click()
            time.sleep(5)  # Allow time for the new content to load

            # Get and print the current URL after the click
            current_url = driver.current_url
            city_links.append((h3_text, current_url))

            # Return to the main page to refresh city blocks for the next iteration
            driver.get(url)
            time.sleep(5)

        progress.stop()

        # Save extracted links to CSV file
        with open('city_links.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["City", "URL"])  # CSV header
            writer.writerows(city_links)

        print("\nCity links have been saved to 'city_links.csv'.")

        driver.quit()  # Close the browser session

    except Exception as e:
        progress.stop()
        print(f"\nError: {e}")
        driver.quit()


def main():
    url = "https://hbl-web.peekaboo.guru/"
    print("Starting extraction process...")
    print("=" * 50)


    extract_city_links(url)

    print("=" * 50)
    print("Extraction process completed!")


if __name__ == "__main__":
    main()
