import os
import json
import random
from unidecode import unidecode

CATEGORIES_PATH = ".\\notebooks\\classify\\categories.txt"

with open(CATEGORIES_PATH, "r", encoding="UTF-8") as file:
    categories_array = file.read().splitlines()

def transliterate_and_clean(category_name):
    """
    Переводит строку в транслит и очищает от запрещенных символов.

    :param category_name: Исходное название категории
    :return: Очищенное и транслитерированное название
    """
    # Переводим в транслит
    transliterated = unidecode(category_name)
    
    # Удаляем запрещенные символы (оставляем только буквы, цифры, пробелы и дефисы)
    cleaned = ''.join(c if c.isalnum() or c in (' ', '_') else '' for c in transliterated)
    
    # Заменяем пробелы на подчеркивания
    cleaned = cleaned.replace(' ', '_')
    
    return cleaned.strip()

def initialize_approved_by_category(correct_categories_folder):
    """
    Инициализирует словарь approved_by_category из файла correct_categories/approved_by_category.json.

    :param correct_categories_folder: Путь к папке с файлами категорий
    :return: Словарь с данными из файла approved_by_category.json
    """
    approved_by_category = {}
    file_path = os.path.join(correct_categories_folder, "approved_by_category.json")

    # Проверяем, существует ли файл
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for clean_category, category_data in data.items():
                    approved_by_category[clean_category] = {
                        "category": category_data["category"],
                        "data": category_data["data"]
                    }
        except json.JSONDecodeError:
            print(f"Ошибка при декодировании JSON из файла '{file_path}'. Пропускаем.")
        except Exception as e:
            print(f"Неожиданная ошибка при обработке файла '{file_path}': {e}")

    return approved_by_category

def save_approved_by_category(approved_by_category, correct_categories_folder):
    """
    Сохраняет словарь approved_by_category в файл correct_categories/approved_by_category.json.

    :param approved_by_category: Словарь с данными для сохранения
    :param correct_categories_folder: Путь к папке для сохранения
    """
    file_path = os.path.join(correct_categories_folder, "approved_by_category.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as outfile:
            json.dump(approved_by_category, outfile, ensure_ascii=False, indent=4)
        print(f"\nСохранено {sum(len(category['data']) for category in approved_by_category.values())} элементов в файл '{file_path}'.")
    except Exception as e:
        print(f"Ошибка при сохранении файла '{file_path}': {e}")

def load_random_elements_and_interact(grouped_data_folder, correct_categories_folder, categories_array):
    """
    Интерактивный терминал для выбора элементов из файлов grouped_data с проверкой на разрешенные категории.

    :param grouped_data_folder: Путь к папке с файлами grouped_data
    :param correct_categories_folder: Путь к папке для сохранения выбранных элементов
    :param categories_array: Массив разрешенных категорий
    """
    # Создаем папку для сохранения результатов, если она не существует
    os.makedirs(correct_categories_folder, exist_ok=True)

    # Инициализируем approved_by_category через файл correct_categories/approved_by_category.json
    approved_by_category = initialize_approved_by_category(correct_categories_folder)

    # Перебираем файлы в папке grouped_data
    for filename in os.listdir(grouped_data_folder):
        file_path = os.path.join(grouped_data_folder, filename)

        # Проверяем, что это файл и он имеет расширение .json
        if os.path.isfile(file_path) and filename.endswith('.json'):
            try:
                # Открываем и читаем файл
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                    # Проверяем, что данные являются списком (массивом)
                    if not isinstance(data, list):
                        print(f"Файл '{filename}' содержит данные, которые не являются массивом. Пропускаем.")
                        continue

                    # Ограничиваем количество проверок до 20 итераций
                    checks_count = 0
                    max_checks = 30

                    category_name = transliterate_and_clean(data[0]["answer"])
                    
                    # Цикл для перебора всех элементов в файле
                    while data and checks_count < max_checks and len(approved_by_category.get(category_name, {}).get("data", [])) < 10:
                        # Выбираем случайный элемент
                        element = random.choice(data)
                        data.remove(element)  # Удаляем элемент из списка, чтобы не повторяться

                        # Выводим элемент в консоль
                        print("\n--- Новый элемент ---")
                        print(json.dumps(element, ensure_ascii=False, indent=4))

                        # Запрашиваем у пользователя подтверждение
                        user_input = input("Одобрить этот элемент? (y/yes/n/no/s/skip или напишите новую категорию): ").strip()
                        checks_count += 1

                        # Обработка команды "s/skip"
                        if user_input.lower() in ('s', 'skip'):
                            print(f"Категория '{category_name}' пропущена.")
                            break  # Прерываем цикл для текущего файла и переходим к следующему

                        # Определяем категорию
                        if user_input.lower() in ('y', 'yes'):
                            # Сохраняем под текущей категорией из answer
                            new_category = element['answer']
                        elif user_input.lower() in ('n', 'no'):
                            print("Элемент отклонен.")
                            continue
                        else:
                            # Пользователь ввел новую категорию
                            new_category = user_input

                        # Проверяем, находится ли категория в массиве разрешенных категорий
                        if new_category not in categories_array:
                            print(f"Категория '{new_category}' не разрешена. Элемент пропущен.")
                            continue

                        # Транслитерируем и очищаем новую категорию
                        clean_category_name = transliterate_and_clean(new_category)
                        element['answer'] = new_category

                        # Добавляем элемент в соответствующую категорию
                        if clean_category_name not in approved_by_category:
                            approved_by_category[clean_category_name] = {
                                "category": new_category,
                                "data": []
                            }
                        approved_by_category[clean_category_name]["data"].append(element)
                        print(f"Элемент добавлен в категорию '{clean_category_name}'.")
                        print(f"Количество элементов в данной категории: {len(approved_by_category[clean_category_name]['data'])}")

                        # Сохраняем одобренные элементы после 20 итераций
                        if checks_count >= max_checks:
                            save_approved_by_category(approved_by_category, correct_categories_folder)

                    save_approved_by_category(approved_by_category, correct_categories_folder)

            except json.JSONDecodeError:
                print(f"Ошибка при декодировании JSON из файла '{filename}'. Пропускаем.")
            except Exception as e:
                print(f"Неожиданная ошибка при обработке файла '{filename}': {e}")

# Укажите путь к папке с файлами grouped_data
grouped_data_folder = ".\\notebooks\\classify\\grouped_data"

# Укажите путь к папке для сохранения выбранных элементов
correct_categories_folder = ".\\notebooks\\classify\\correct_categories"

# Запускаем интерактивный терминал
load_random_elements_and_interact(grouped_data_folder, correct_categories_folder, categories_array)