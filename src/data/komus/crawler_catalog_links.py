from driver import get_driver, load_page
from text_utils import get_category_name
from undetected_chromedriver import Chrome

from selenium.webdriver.remote.webdriver import By


CHECKED_PAGES = set()

FILEPATH = "src\data\komus\categories"

def get_catalog_links(driver: Chrome, catalog_link: str) -> set[str]:
    res: list[str] = set()

    clear_link = catalog_link.split('?')[0]

    if clear_link in CHECKED_PAGES:
        return set()
    
    CHECKED_PAGES.update({clear_link})

    print(f"check page: {clear_link}")

    load_page(driver, clear_link, "catalog__header")

    categories = driver.find_elements(By.CLASS_NAME, "categories__name")

    if not categories:
        with open(f"{FILEPATH}\\all_temp.txt", 'a') as file:
            file.write(f"{clear_link}\n")

        return {catalog_link}
    else:
        categories_link = [category.get_attribute('href') for category in categories]

        for link in categories_link:
            res.update(get_catalog_links(driver, link))

    return res

if __name__ == "__main__":
    driver = get_driver()

    links = get_catalog_links(driver, "https://www.komus.ru/katalog/novogodnie-tovary/c/13436/")
    
    with open(f"{FILEPATH}\\all.txt") as file:
        file.write("\n".join(links))

    # for CATEGORY_CATALOG_LINK in links:
    #     CATEGORY_NAME = get_category_name(CATEGORY_CATALOG_LINK)
        
    #     links = get_catalog_links(driver, CATEGORY_CATALOG_LINK)

    #     print(*links, sep="\n")

    #     with open(f"{FILEPATH}\{CATEGORY_NAME}.txt", 'w') as file:
    #         file.write("\n".join(links))
    
    driver.quit()
