from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from typing import List

options = webdriver.ChromeOptions()

# minimize logs
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument('log-level=3')

# 
options.add_argument('--disable-extensions')
options.add_argument('--disable-popup-blocking')

options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2  # Отключение загрузки изображений
})

driver = webdriver.Chrome(options=options)

def write_buffer(list_products: List[str], index: int):
    with open(f".\\src\\data\\napolke{index}.txt", 'a', encoding="utf-8") as file:
        file.write('\n'.join(list_products) + '\n')

if __name__ == '__main__':
    index = 0 # индекс(нужен для запуска в нескольких интерпретаторах)
    offset = 0 # смещение в случае прерывание работы
    batch = 6000 # количество сохраненных продуктов
    page_product_size = 60 # количество продуктов на одной странице

    products = []

    start, end = batch * index + offset, min(batch * (index + 1) - 1, 41886)

    for i in range(start, end, 60):
        driver.get(f"https://napolke.ru/catalog?offset={i}")
        list_products = [product.text for product in driver.find_elements(By.CLASS_NAME, "product-title")]
        products += list_products

        write_buffer(list_products, index)
        print(f"{i}: {list_products}")

    driver.quit()