from typing import Any, Dict, List, Tuple
import math
import logging
from random import sample

from tqdm import tqdm
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate
)

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain_core.runnables import Runnable

from dotenv import load_dotenv

import os
import json
from typing import List
import datetime


load_dotenv(".env")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

COL_ATTRIBUTES: str = 'attributes'
BASE_PATH_FOR_CORRECT_BATCH: str = "./data/processed/"

ANSWER_COMMAND: str = "Окончательный ответ:"

BATCH_SIZE = int(os.environ['BATCH_SIZE']) if 'BATCH_SIZE' in os.environ else 16

TOTAL_AUGMENTED_ITEMS = 8000

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Загружаем данные, соответствие атрибутного состава для которого нам нужно найти
with open("./data/dataset_1.0.json", "r", encoding="utf-8") as file:
    data_metrics = json.load(file)

# Загружаем примеры, которые пойдут во few-shot
with open("./data/augment_examples.json", "r", encoding="UTF-8") as file:
    examples = json.load(file)

examples_str = "\n".join([f"""
{i+1})Оригинальная товарная позиция: {product["clean_item"]}
Аугментированная товарная позиция: {product['original_item']}
""".strip() for i, product in enumerate(examples)])

print(len(data_metrics))

## Загрузка параметров модели

model_params = {
    "base_url": os.getenv("OPENAI_BASE_URL"),
    "model_name": os.getenv("OPENAI_MODEL_NAME"),
    "api_key": os.getenv("OPENAI_API_KEY"),
    "temperature": 0
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_REGION:
#     raise ValueError("AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_REGION must be set for saving data into s3")

llm = ChatOpenAI(**model_params)

def create_model_prompts(system_prompt: str,
                         user_prompt: str) -> ChatPromptTemplate:
    system_prompt = SystemMessagePromptTemplate.from_template(system_prompt)
    user_prompt = HumanMessagePromptTemplate.from_template(user_prompt)
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_prompt,
         user_prompt]
    )
    return chat_prompt

def get_batch(data_metrics,
              examples_str,
              parser = SimpleJsonOutputParser()):
    category_map = {}

    for i, product in enumerate(data_metrics):
        if product["category"] not in category_map:
            category_map[product["category"]] = []
        
        product["index_item"] = i

        category_map[product["category"]].append(product)

    sample_data = []
    len_category_sample_products = TOTAL_AUGMENTED_ITEMS // len(category_map.keys())

    for category, products in category_map.items():
        sample_products = sample(products, len_category_sample_products) if len_category_sample_products < len(products) else products
        sample_data += sample_products

    return [
        {
            "examples": examples_str if examples_str else "Без примеров",
            "format_instructions": parser.get_format_instructions(),
            "problem_title": product["title"],
            "index_item": product["index_item"] 
        } for product in sample_data
    ]

def postprocessing(result: List[Dict[str, Any]],
                   parser: PydanticOutputParser) -> List[Dict[str, Any]]:
    format_result = [parser.invoke(item.split(ANSWER_COMMAND)[1]).answer for item in result]
    return format_result

def save_results(results: List[Any],
                 path: str):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False)


def batched_processing(dataset: List[Dict[str, Any]],
                       chain: Runnable,
                       parser: PydanticOutputParser,
                       batch_size: int = 256) -> Dict[int, Dict[str, Any]]:
    # Словарь для хранения результатов для каждого батча
    # Ключ - номер батча, значение 3 ключа с результатами:
    # 1. batch - сами значения батча, которые поступили в цепочку
    # 2. result - результаты, которые получили из цепочки
    # 3. result_without_postprocessing - результаты, которые получили из цепочки без постпроцессинга
    map_batch_id_to_result = []
    i_end = math.ceil(len(dataset) / batch_size)
    logger.info(f"Processing {len(dataset)} products in {i_end} batches")
    for i in tqdm(range(i_end)):
        batch = dataset[i * batch_size:(i + 1) * batch_size]
        result = []
        format_result = []
        try:
            result = chain.batch(batch)
            format_result = postprocessing(result, parser) # Получаем ключи, которы нужно оставить в характеристиках продукта
        except Exception as e:
            logger.error(f"Error in batch {i}: {e}")

        map_batch_id_to_result.append({
            'index_items': [item["index_item"] for item in batch],
            'batch': batch,
            'result': format_result,
            'result_without_postprocessing': result
        })
        save_results(map_batch_id_to_result, f"{BASE_PATH_FOR_CORRECT_BATCH}/map_batch_id_to_result.json")

    return map_batch_id_to_result


class AugmentationResultResponse(BaseModel):
    answer: str = Field(..., description="Аугментированная позиция")
    changes: List[Tuple[str, str]] = Field(..., description="Список изменений при аугментации. Каждая пара представляет собой кортеж из двух строк. Первая строка - до изменений, вторая - после изменений. Обе строки не могут быть пустыми.")

parser = PydanticOutputParser(pydantic_object=AugmentationResultResponse)

SYSTEM_PROMPT = """
Проведи аугментацию над наименованием товарной позиции.

Примеры:
{examples}

Правила аугментации:
1. **Сохранение всех деталей**  
   - При создании вариаций товарной позиции **все исходные детали должны быть сохранены**.  
   - Никакие элементы наименования товарной позиции не должны быть упущены.
2. **Отсутствие добавления новых деталей**  
   - В аугментированных вариантах **запрещено добавлять новые сведения**, которые отсутствуют в исходной товарной позиции.  
   - Например, если цвет товара не указан, его нельзя добавить в описание.
3. **Не проводи транслитерацию важных деталей товарной позиции**  
   - Не аугментируй детали товарной позиции, по которым можно точно идентифицировать товарную позицию (пример: модель, компания-производитель, артикул)
4. **Не проводи частичную транслитерацию**

Подумай шаг за шагом. 

Правила для формирования ответа:
1. **Рассуждение должно быть текстовым.**  
   - Рассуждения должны быть представлены в виде сплошного текста. Блоки кода в ходе рассуждения запрещены.
   - Все логические шаги, анализы и выводы должны быть изложены четко и последовательно.
2. **Финальный ответ должен быть представлен в виде JSON-объекта, заключённого в один блок кода.**  
   - Финальный ответ должен быть корректным JSON-объектом, который заключается в один блок кода (используя три обратных апострофа ```).
   - Внутри JSON-объекта не должно быть дополнительных объяснений или текстовых комментариев.
3. **Фраза "Окончательный ответ" должна предварять блок кода с JSON-объектом.**  
   - Перед блоком кода с JSON-объектом должна быть написана фраза **"Окончательный ответ:"** (без кавычек в самой фразе).  
   - Между фразой и блоком кода не должно быть пустых строк.

Формат ответа должен соответствовать этому: {format_instructions}
""".strip()

USER_PROMPT =  """
Товарная позиция: {problem_title}
""".strip()

prompt = create_model_prompts(SYSTEM_PROMPT, USER_PROMPT)

prepared_dataset = get_batch(data_metrics, examples_str, parser)

augment_chain = prompt | llm | StrOutputParser()

map_batch_id_to_result = batched_processing(prepared_dataset, augment_chain, parser)

logger.info(f"Обработка завершена")
