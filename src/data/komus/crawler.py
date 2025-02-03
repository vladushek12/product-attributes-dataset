from fileinput import filename
import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from undetected_chromedriver import Chrome

from driver import get_driver, load_page
from text_utils import get_category_name, create_params

from time import sleep
from math import ceil 
from json import dump
from os.path import exists
from os import remove

# CATALOG_LINK = "https://www.komus.ru/katalog/khozyajstvennye-tovary/meshki-i-emkosti-dlya-musora/korziny-dlya-bumag/c/10171/?from=menu-v1-kantstovary"
# FILENAME = "korziny-dlya-bumag"


def get_links(driver: Chrome, catalog_link: str) -> list[str]:
    clear_catalog_link = catalog_link.split('?')[0]

    load_page(driver,
              clear_catalog_link + f"?{create_params(listingMode='GRID')}",
              wait_element_class="catalog__header-sup")

    count_elements = int(driver.find_element(By.CLASS_NAME, "catalog__header-sup").text)

    count_pages = ceil(float(count_elements)/30)
    print(f"count pages:{count_pages}")

    links = []

    for page in range(count_pages):
        links += get_links_page(driver, clear_catalog_link + f"?{create_params(listingMode='GRID', page=page)}")

    return links


def get_links_page(driver: Chrome, catalog_link: str):
    load_page(driver,
              catalog_link,
              wait_element_class="js-article-link")

    product_items = driver.find_elements(By.CLASS_NAME, "js-article-link")
    product_links = [product.get_attribute('href').split('?')[0] for product in product_items]

    return product_links


def parse_product_page(driver: Chrome, product_link: str):
    load_page(driver,
              product_link + f"?{create_params(tabId='specifications')}",
              wait_element_class="product-details-page__title")

    title = driver.find_element(By.CLASS_NAME, "product-details-page__title").text

    names = [item.text for item in driver.find_elements(By.CLASS_NAME, "product-classification__name") if item.text]

    feature = [item.text for item in driver.find_elements(By.CLASS_NAME, "product-classification__feature") if item.text]
    values = [item.text for item in driver.find_elements(By.CLASS_NAME, "product-classification__values") if item.text]

    top_tech = list(zip(names, values[:len(names)]))
    bottom_tech = list(zip(feature, values[len(names):]))

    res = {
        'link': product_link,
        'title': title,
        'attributes': {}
    }

    for key, value in top_tech:
        res['attributes'][key] = value

    for key, value in bottom_tech:
        res['attributes'][key] = value

    return res

if __name__ == "__main__":
    CATALOG_LINK = input()
    FILENAME = get_category_name(CATALOG_LINK)
    FILEPATH = "src\data\komus\data"

    if exists(f"{FILEPATH}\{FILENAME}.json"):
        quit()

    driver = get_driver()

    if exists(f"{FILEPATH}\{FILENAME}_links.txt"):
        with open(f"{FILEPATH}\{FILENAME}_links.txt") as file:
            links = file.read().split("\n")
    else:
        links = get_links(driver, CATALOG_LINK)

        with open(f"{FILEPATH}\{FILENAME}_links.txt", 'w') as file:
            file.write("\n".join(links))


    def save_json(filepath, data):
        with open(filepath, "w", encoding="utf-8") as file:
            dump(data, file, ensure_ascii=False)

    print(*links, sep="\n")

    products = []

    for i, product_link in enumerate(links):
        print(i, product_link)

        product = parse_product_page(driver, product_link)
        products.append(product)

        if i % 10 == 0:
            save_json(f"{FILEPATH}\{FILENAME}_temp.json", products)

    save_json(f"{FILEPATH}\{FILENAME}.json", products)
    remove(f"{FILEPATH}\{FILENAME}_temp.json")

    driver.close()
