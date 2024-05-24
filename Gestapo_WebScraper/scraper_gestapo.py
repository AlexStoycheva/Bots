import openpyxl
import time
import argparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)

headers = [
    "ЕИК/ПИК",
    "Наименование",
    "Правна форма",
    "Регистрация",
    "Регистрация по ДДС",
    "Капитал",
    "Седалище",
    "Телефон",
    "Ел. поща",
    "Основна дейност",
    "Управители",
]


def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Scrape company information and save to Excel."
    )
    parser.add_argument(
        "--input", required=True, help="Path to the input file containing companies IDs."
    )
    parser.add_argument(
        "--output", required=False, default="companies.xlsx", help="Path to the output file containing companies info."
    )
    args = parser.parse_args()

    return args


def check_exists_by_xpath(xpath):

    try:
        driver.find_element(By.XPATH, xpath)

    except NoSuchElementException:
        return False

    return True


def scrape_company_info(driver, line):

    input_element = driver.find_element("name", "name_org")
    input_element.send_keys(line + Keys.ENTER)

    company_details = driver.find_element(
        By.XPATH, '//*[@id="responsive-table"]/table/tbody/tr[2]/td[1]'
    ).text
    description = driver.find_element(
        By.XPATH, '//*[@id="responsive-table"]/table/tbody/tr[2]/td[2]'
    ).text
    managers = driver.find_element(
        By.XPATH, '//*[@id="responsive-table"]/table/tbody/tr[2]/td[3]'
    ).text

    eik_pik = "-"
    naimenovanie = "-"
    pravna_forma = "-"
    registration = "-"
    registration_dds = "-"
    kapital = "-"
    sedalishte = "-"
    telefon = "-"
    email = "-"
    osn_deinost = "-"
    upravitel = "-"

    for item in company_details.split("\n"):
        if item.startswith("ЕИК/ПИК:"):
            eik_pik = item.split(":")[1].strip()
        elif item.startswith("Наименование:"):
            naimenovanie = item.split(":")[1].strip()
        elif item.startswith("Правна форма:"):
            pravna_forma = item.split(":")[1].strip()
        elif item.startswith("Регистрация:"):
            registration = item.split(":")[1].strip()
        elif item.startswith("Регистрация по ДДС:"):
            registration_dds = item.split(":")[1].strip()
        elif item.startswith("Капитал:"):
            kapital = item.split(":")[1].strip()
        elif item.startswith("Седалище:"):
            sedalishte = item.split(":")[1].strip()
        elif item.startswith("Телефон:"):
            telefon = item.split(":")[1].strip()
        elif item.startswith("Електронна поща:"):
            email = item.split(":")[1].strip()
        else:
            continue

    if len(description.split("\n")) >= 1 and description.split("\n")[0].startswith(
        "Основна дейност ("
    ):
        osn_deinost = description.split("\n")[0].split(":")[1].split("-")[0].strip()

    if len(managers.split("\n")) >= 2:
        upravitel = managers.split("\n")[1]

    time.sleep(2)

    input_element = driver.find_element("name", "name_org")
    input_element.clear()

    time.sleep(1)

    return [
        eik_pik,
        naimenovanie,
        pravna_forma,
        registration,
        registration_dds,
        kapital,
        sedalishte,
        telefon,
        email,
        osn_deinost,
        upravitel,
    ]


def write_to_excel(file_path, data):

    wb = openpyxl.Workbook()
    ws = wb.active

    ws.append(headers)

    for row in data:
        ws.append(row)

    wb.save(file_path)


def main():

    args = parse_arguments()

    company_data = []
    driver.get("https://gestapo.bg/Search")

    try:
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/div[2]/button[1]")
            )
        ).click()
    except:
        pass

    time.sleep(2)

    with open(args.input, "r") as f:
        company_names = [line.strip() for line in f.readlines() if line.strip() != ""]

    for company_name in company_names:
        company_info = scrape_company_info(driver, company_name)
        company_data.append(company_info)
        time.sleep(1)

    write_to_excel(args.output, company_data)

    driver.quit()


if __name__ == "__main__":
    main()
