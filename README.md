Product attributes dataset
==============================

Тема работы: "Технология подготовки датасета для обучения большой языковой модели по извлечению атрибутов из товарных позиций".

В рамках данной работы будет создана технология для создания датасета.

--------

План работы: 

1. Сбор данных при помощи web-scraping. [папка](/src/data/komus)
2. Очистка данных при помощи LLM. [ноутбук](/notebooks/test_similarity_prompts.ipynb), [скрипт](/src/models/attributes_mapper.py)
3. Аугментация данных. [ноутбук](/notebooks/few_shot_augmentation.ipynb), [скрипт](/src/models/augmentator.py)
4. Определение системы категорий товаров [папка](/notebooks/classify)

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
