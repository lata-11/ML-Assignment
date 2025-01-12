import requests
from bs4 import BeautifulSoup
import csv

# Base URL for Redfin search page
url = "https://www.redfin.com/city/18142/FL/Tampa"

# Headers for the request to simulate a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
}

# Send a GET request to fetch the search page
response = requests.get(url, headers=headers)
properties = []

if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all home cards on the search page
    homecards = soup.find_all("div", class_="HomeCardContainer")

    for card in homecards:
        try:
            # Extract the basic details
            if card.find("a", class_="link-and-anchor"):
                link = card.find("a", class_="link-and-anchor")["href"]
                full_link = "https://www.redfin.com" + link
                price = card.find("span", class_="bp-Homecard__Price--value").text.strip()
                beds = card.find("span", class_="bp-Homecard__Stats--beds").text.strip()
                baths = card.find("span", class_="bp-Homecard__Stats--baths").text.strip()
                address = card.find("div", class_="bp-Homecard__Address").text.strip()

                print("Fetching details for:", full_link)

                # Fetch the property page for additional details
                property_response = requests.get(full_link, headers=headers)
                if property_response.status_code == 200:
                    property_soup = BeautifulSoup(property_response.content, "html.parser")

                    # Scrape the "About This Home" section
                    about_section = property_soup.find("section", {"id": "about-this-home-scroll"})
                    about_home = ""
                    key_details = []

                    if about_section:
                        # Extract the marketing remarks
                        remarks = about_section.find('div', class_='remarks')
                        about_home = remarks.get_text(strip=True) if remarks else "No Remarks Found"

                        # Extract key details
                        key_details_rows = about_section.find_all('div', class_='keyDetails-row')
                        for detail in key_details_rows:
                            label = detail.find('span', class_='keyDetails-label')
                            value = detail.find('div', class_='keyDetails-value')
                            label_text = label.get_text(strip=True) if label else "No Label"
                            value_text = value.get_text(strip=True) if value else "No Value"
                            key_details.append(f"{label_text}: {value_text}")

                    # Scrape Sale and Tax History
                    sale_and_tax_history = {}
                    sale_and_tax_section = property_soup.find("section", {"id": "property-history-scroll"})
                    if sale_and_tax_section:
                        sale_tabs = sale_and_tax_section.find_all("div", class_="timeline-content")
                        for tab in sale_tabs:
                            sale_tax_header = tab.find("h4", class_="section-header")
                            if sale_tax_header:
                                date = sale_tax_header.get_text(strip=True)
                                event_row = tab.find("div", class_="PropertyHistoryEventRow")
                                if event_row:
                                    price_col = event_row.find("div", class_="price-col")
                                    price = price_col.get_text(strip=True) if price_col else "No Price"
                                    sale_and_tax_history[date] = price
                            
                    # Print extracted details
                    print("Link:", full_link)
                    print("Price:", price)
                    print("Beds:", beds)
                    print("Baths:", baths)
                    print("Address:", address)
                    print("About This Home:", about_home)
                    print("Key Details:", "; ".join(key_details))
                    print("Sale and Tax History:", sale_and_tax_history)
                    print()

                    # Append the data to the properties list
                    properties.append({
                        "Price": price,
                        "Beds": beds,
                        "Baths": baths,
                        "Address": address,
                        "Link": full_link,
                        "About This Home": about_home,
                        "Key Details": "; ".join(key_details),
                        "Sale and Tax History": "; ".join([f"{date}: {price}" for date, price in sale_and_tax_history.items()])
                    })
        except Exception as e:
            print(f"Error processing a home card: {e}")
            continue

# Save the data to a CSV file
csv_filename = "redfin_properties_with_sale_and_tax_history.csv"
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["Price", "Beds", "Baths", "Address", "Link", "About This Home", "Key Details", "Sale and Tax History"])
    writer.writeheader()
    writer.writerows(properties)

print(f"Data saved to {csv_filename}")
