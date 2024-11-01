#Beautiful Soup: A library for parsing HTML and XML documents,
#useful for web scraping and data extraction.


import requests
from bs4 import BeautifulSoup
# Scraping a website for links
url = "http://www.google.com"
# url = "https://www.hbl.com/personal/cards/hbl-deals-and-discounts"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
links = soup.find_all('a')
for link in links:
 print(f"Link: {link.get('href')}")