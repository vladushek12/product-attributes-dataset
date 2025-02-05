import re
import glob

from pathlib import Path

FILEPATH_DATA = "src\data\komus\data"
FILEPATH_CATEGORIES = "src\data\komus\categories"

with open(f"{FILEPATH_CATEGORIES}\\all.txt", "r", encoding="utf-8") as file:
    data = file.read().split("\n")

complete_categories = [str(Path(file).stem) for file in glob.glob(f"{FILEPATH_DATA}\*.json")]

def get_index(filename: str) -> int:
    pattern = re.compile(rf".*/{filename}-?/c/.*")
    for i, link in enumerate(data):
        if re.match(pattern, link):
            return i

    return -1

for category in complete_categories:
    index = get_index(category)

    if index > -1:
        data.pop(index)
    else:
        print(f"error on {category}")

data = [f'"{link}"' for link in data]

length = len(data)
print(f"length : {length}")
step = 20

with open("src\data\komus\categories\\packages.txt", "w", encoding='utf-8') as file:
    for i in range(length // step):
        file.write(".\src\data\komus\script.bat "+ " ".join(data[i*step:min(length, (i+1)*step)]) + "\n")