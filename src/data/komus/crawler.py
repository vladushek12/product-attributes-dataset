import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import By
from time import sleep

from math import ceil 

options = uc.ChromeOptions()

# minimize logs
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument('log-level=3')

# disable
options.add_argument('--disable-extensions')
options.add_argument('--disable-popup-blocking')

options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2  # Отключение загрузки изображений
})

driver = uc.Chrome(options=options)


def load_page(link: str):
    driver.get(link)
    sleep(1)


def create_params(**params):
    return "&".join([f"{key}={value}" for key, value in params.items()])


def get_links(catalog_link: str):
    clear_catalog_link = catalog_link.split('?')[0]

    load_page(clear_catalog_link + f"?{create_params(listingMode='GRID')}")

    count_elements = int(driver.find_element(By.CLASS_NAME, "catalog__header-sup").text)

    count_pages = ceil(float(count_elements)/30)
    print(count_pages)

    links = []

    for page in range(count_pages):
        links += get_links_page(clear_catalog_link + f"?{create_params(listingMode='GRID', page=page)}")

    return links


def get_links_page(catalog_link: str):
    load_page(catalog_link)

    product_items = driver.find_elements(By.CLASS_NAME, "js-article-link")

    product_links = [product.get_attribute('href').split('?')[0] for product in product_items]

    return product_links


def parse_product_page(product_link: str):
    load_page(product_link + f"?{create_params(tabId='specifications')}")

    title = driver.find_element(By.CLASS_NAME, "product-details-page__title").text

    names = [item.text for item in driver.find_elements(By.CLASS_NAME, "product-classification__name") if item.text]

    feature = [item.text for item in driver.find_elements(By.CLASS_NAME, "product-classification__feature") if item.text]
    values = [item.text for item in driver.find_elements(By.CLASS_NAME, "product-classification__values") if item.text]

    top_tech = list(zip(names, values[:len(names)]))
    bottom_tech = list(zip(feature, values[len(names):]))

    # for left, right in top_tech:
    #     print(left, right)

    # for left, right in bottom_tech:
    #     print(left, right)

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

# product = parse_product_page('https://www.komus.ru/katalog/mebel/ofisnye-kresla-i-stulya/kresla-dlya-rukovoditelej/kresla-dlya-rukovoditelej-standartnye/kreslo-dlya-rukovoditelya-easy-chair-655-lt-ttw-chernoe-setka-tkan-plastik-/p/1645881/?tabId=specifications')

links = get_links("https://www.komus.ru/katalog/kantstovary/kalkulyatory/c/970/")

print(*links, sep="\n")
print(len(links))

driver.close()