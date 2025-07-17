import argparse
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup Chrome driver
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
# Setup Chrome driver
driver = webdriver.Chrome(options=options)  # Ensure chromedriver is in PATH

BASE_URL = "https://www.car-part.com/"

def scrape_results_from_current_page(sub_option_label, year, model, part):
    results = []
    table = driver.find_element(By.XPATH, "//table[@border='1' and @cellpadding='4']")
    rows = table.find_elements(By.TAG_NAME, "tr")[1:-1]  # Skip first and last (header/footer)

    print(f"Length of data: {len(rows)}")

    for row in rows:
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 7:
                continue

            year_part_model = cells[0].get_attribute("innerHTML").split("<br>")
            row_year = year_part_model[0].strip() if len(year_part_model) > 0 else ""
            row_part = year_part_model[1].strip() if len(year_part_model) > 1 else ""
            row_model = year_part_model[2].strip() if len(year_part_model) > 2 else ""

            if int(row_year) != int(year) or row_model != model or row_part != part:
                continue

            description = cells[1].text.strip()

            part_grade_lines = cells[3].get_attribute("innerHTML").split("<br>")
            part_grade = part_grade_lines[0].strip() if part_grade_lines else ""
            part_grade_score = part_grade_lines[1].strip() if len(part_grade_lines) > 1 else ""

            stock_info = cells[4].get_attribute("innerHTML").split("<br>")
            stock_num = stock_info[0].strip()
            co2_elem = BeautifulSoup(cells[4].get_attribute("innerHTML"), "html.parser").find("div")
            co2_saving = co2_elem.text.strip() if co2_elem else ""

            price = cells[5].text.split("\n")[0].strip()
            if price.startswith('$'):
                price = price[1:]
            dealer_info = cells[6].text.strip()

            is_oem = "TRUE" if "oem" in description.lower() else "FALSE"
            is_damaged = "TRUE" if "damage" in description.lower() else "FALSE"

            results.append({
                "Year": row_year,
                "Model": row_model,
                "Part": row_part,
                "Sub Option": sub_option_label,
                "Description": description,
                "Grade": part_grade + part_grade_score,
                "Stock": stock_num,
                "is_OEM": is_oem,
                "is_Damaged": is_damaged,
                # "CO2 Savings": co2_saving,
                "Price": price,
                "Contact Info": dealer_info
            })
        except Exception as e:
            print(f"Error in Data List Page as {e}")

    return results

def process(year, model, part, country):
    all_results = []
    driver.get(BASE_URL)

    # Fill the initial form once to get sub-options
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "userDate")))
    Select(driver.find_element(By.NAME, "userDate")).select_by_visible_text(year)
    Select(driver.find_element(By.NAME, "userModel")).select_by_visible_text(model)
    Select(driver.find_element(By.NAME, "userPart")).select_by_visible_text(part)
    Select(driver.find_element(By.NAME, "userLocation")).select_by_visible_text(country)
    Select(driver.find_element(By.NAME, "userPreference")).select_by_visible_text("Price")
    driver.find_element(By.NAME, "userZip").clear()
    driver.find_element(By.XPATH, "//input[@type='image' and @name='Search Car Part Inventory']").click()


    # Wait for sub-option radio buttons to load
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.NAME, "dummyVar")))
    radio_buttons = driver.find_elements(By.NAME, "dummyVar")
    labels = driver.find_elements(By.XPATH, "//input[@name='dummyVar']/following-sibling::label")
    sub_option_count = len(radio_buttons)

    for i in range(sub_option_count):
        try:
            driver.get(BASE_URL)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "userDate")))
            Select(driver.find_element(By.NAME, "userDate")).select_by_visible_text(year)
            Select(driver.find_element(By.NAME, "userModel")).select_by_visible_text(model)
            Select(driver.find_element(By.NAME, "userPart")).select_by_visible_text(part)
            Select(driver.find_element(By.NAME, "userLocation")).select_by_visible_text(country)
            Select(driver.find_element(By.NAME, "userPreference")).select_by_visible_text("Price")
            driver.find_element(By.NAME, "userZip").clear()
            driver.find_element(By.XPATH, "//input[@type='image' and @name='Search Car Part Inventory']").click()

            # Wait for sub-options again
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.NAME, "dummyVar")))
            radio_buttons = driver.find_elements(By.NAME, "dummyVar")
            labels = driver.find_elements(By.XPATH, "//input[@name='dummyVar']/following-sibling::label")

            if i >= len(radio_buttons):
                break

            # Extract part name from label for context
            label_text = labels[i].text.strip()
            radio_buttons[i].click()
            print(f"------------ Current Sub Option {label_text} ------------")
            driver.find_element(By.XPATH, "//input[@type='image' and @name='Search Car Part Inventory']").click()

            # Wait for results table
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//table[@border='1' and @cellpadding='4']//tr")))
            # Page 1
            all_results.extend(scrape_results_from_current_page(label_text, year, model, part))

            # Get pagination links (skip page 1 since it's already scraped)
            pagination_links = driver.find_elements(By.XPATH, "//div[.//b[contains(text(), 'Additional Result Pages')]]//table//a")
            print(len(pagination_links))
            page_count = len(pagination_links)
            for page_index in range(page_count):
                try:
                    links = driver.find_elements(By.XPATH, "//div[.//b[contains(text(), 'Additional Result Pages')]]//table//a")
                    if page_index >= len(links):
                        break

                    page_text = links[page_index].text.strip()
                    if not page_text.isdigit():
                        continue
                    print(f"➡️  Clicking page {page_text} for sub-option '{label_text}'")

                    links[page_index].click()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table[@border='1' and @cellpadding='4']//tr")))
                    all_results.extend(scrape_results_from_current_page(label_text, year, model, part))

                except Exception as e:
                    print(f"⚠️ Error on pagination page {page_index+2}: {e}")
                    continue

        except Exception as e:
            print(f"Error in Sub Option Handling as {e}")

    driver.quit()
    return all_results

def run_scraper(year: str, model: str, part: str, country: str) -> list[dict]:
    results = process(year, model, part, country)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--part", required=True)
    parser.add_argument("--country", required=True)
    args = parser.parse_args()

    results = process(args.year, args.model, args.part, args.country)
    print("✅ Extracted and saved to car_part_results.csv")