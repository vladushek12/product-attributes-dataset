from selenium.webdriver.remote.webdriver import By
from undetected_chromedriver import Chrome

from driver import custom_chrome_driver, load_page
from text_utils import get_category_name, create_params, fix_category_name

from math import ceil 
from json import dump, load
from os.path import exists
from os import remove
import sys


def get_header_catalog(driver: Chrome):
    """Функция для получения загаловка каталога на русском языке. Работает на прогруженной странице.

    Args:
        driver (Chrome): Драйвер Chrome браузера.

    Returns:
        tuple[str, int]: Возвращает название и количество элементов, которое хранится в загаловке на странице.
    """
    category_name = driver.find_element(By.CLASS_NAME, "catalog__header").text
    return fix_category_name(category_name)


def get_links(driver: Chrome, catalog_link: str) -> list[str]:
    """Функция которая обрабатывает каталог и возвращает ссылки на продукты

    Args:
        driver (Chrome): Драйвер Chrome браузера.
        catalog_link (str): Ссылка на каталог.

    Returns:
        tuple[str, list[str]: Возвращает название каталога и список ссылок на продукты.
    """
    clear_catalog_link = catalog_link.split('?')[0]

    load_page(driver,
              clear_catalog_link + f"?{create_params(listingMode='GRID')}",
              wait_element_class="catalog__header")

    category_name, count_elements = get_header_catalog(driver)

    count_pages = ceil(float(count_elements)/30)
    print(f"count pages:{count_pages}")

    links = []

    for page in range(count_pages):
        links += get_links_page(driver, clear_catalog_link + f"?{create_params(listingMode='GRID', page=page)}")

    return category_name, links


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


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as file:
        dump(data, file, ensure_ascii=False)


if __name__ == "__main__":
    # Получаем ссылки из аргументов при вызове
    CATALOG_LINKS = sys.argv[1:]
    #filepath for save data
    FILEPATH = "src\data\komus\data"

    with custom_chrome_driver() as driver:
        # Проходимся в цикле по ссылкам
        for CATALOG_LINK in CATALOG_LINKS:
            FILENAME = get_category_name(CATALOG_LINK)
            
            category_name_rus = ""

            json_dump = {
                "category_name": "",
                "count": 0,
                "products": []
            }

            print(f"category: {FILENAME}")

            # Проверка на то, готов ли уже файл по данной категории
            if exists(f"{FILEPATH}\{FILENAME}.json"):
                print(f"category is done")
                continue

            # В случае появления ошибки ссылки с товарами уже сохранены поэтому их можно загрузить из файла
            if exists(f"{FILEPATH}\{FILENAME}_links.txt"):
                with open(f"{FILEPATH}\{FILENAME}_links.txt", "r") as file:
                    links = file.read().split("\n")  

                load_page(driver, CATALOG_LINK, "catalog__header")
                category_name_rus, _ = get_header_catalog(driver)
            else:
                category_name_rus, links = get_links(driver, CATALOG_LINK)

                with open(f"{FILEPATH}\{FILENAME}_links.txt", 'w') as file:
                    file.write("\n".join(links))

            if exists(f"{FILEPATH}\{FILENAME}_temp.json"):
                with open(f"{FILEPATH}\{FILENAME}_temp.json", "r", encoding="utf-8") as file:
                    json_dump["products"] = load(file)

                print(f"temp file is found for {FILENAME}")
                print(f"category name: {category_name_rus}")
                print(f'count checked products {len(json_dump["products"])}')
            json_dump["category_name"] = category_name_rus
            json_dump["count"] = len(links)

            products: list[dict] = json_dump["products"]
            print(f"count links: {json_dump['count']}")

            for i, product_link in enumerate(links[len(json_dump["products"]):], start=len(products)+1):
                product = parse_product_page(driver, product_link)
                products.append(product)

                if i % 20 == 0:
                    print(f"{i} : {json_dump['count']}")
                    save_json(f"{FILEPATH}\{FILENAME}_temp.json", products)

            save_json(f"{FILEPATH}\{FILENAME}.json", json_dump)
            if exists(f"{FILEPATH}\{FILENAME}_temp.json"):
                remove(f"{FILEPATH}\{FILENAME}_temp.json")
            
