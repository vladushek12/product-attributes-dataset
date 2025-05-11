import re
import glob

from pathlib import Path
from text_utils import get_category_name

FILEPATH_DATA = "src\data\komus\data"
FILEPATH_CATEGORIES = "src\data\komus\categories"

with open(f"{FILEPATH_CATEGORIES}\\all.txt", "r", encoding="utf-8") as file:
    links = file.read().split("\n")
    category_names = [get_category_name(link) for link in links]

complete_categories = [str(Path(file).stem) for file in glob.glob(f"{FILEPATH_DATA}\*.json")]

def get_index(filename: str) -> int:
    for i, category in enumerate(category_names):            
        if filename == category:
            # print(filename, category, category_names[i], links[i])
            return i

    return -1

for category in complete_categories:
    index = get_index(category)
    if index > -1:
        links.pop(index)
        category_names.pop(index)
    else:
        print(f"error on {category}")

links = [f'"{link}"' for link in links]

length = len(links)
print(f"length : {length}")
step = 50

with open("src\data\komus\categories\\packages.txt", "w", encoding='utf-8') as file:
    for i in range(length // step):
        file.write(".\src\data\komus\script.bat "+ " ".join(links[i*step:min(length, (i+1)*step)]) + "\n")