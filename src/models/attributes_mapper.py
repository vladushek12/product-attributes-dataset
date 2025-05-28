from typing import Any, Dict, List
import math
import logging

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


AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

COL_ATTRIBUTES: str = 'attributes'
BASE_PATH_FOR_CORRECT_BATCH: str = "./data/processed/correct_batch_result"
BASE_PATH_FOR_INCORRECT_BATCH: str = "./data/processed/incorrect_processed_batch"

BATCH_SIZE = int(os.environ['BATCH_SIZE']) if 'BATCH_SIZE' in os.environ else 16

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Загружаем данные, соответствие атрибутного состава для которого нам нужно найти
with open("./data/dataset.json", "r", encoding="utf-8") as file:
    data_metrics = json.load(file)

# Загружаем примеры, которые пойдут во few-shot
with open("./data/examples.json", "r", encoding="UTF-8") as file:
    examples = json.load(file)
examples_str = "\n".join([f"""
{i+1})Название товара: {product["title"]}.
Характеристики: {json.dumps(product[COL_ATTRIBUTES], ensure_ascii=False)}.
Ответ: {json.dumps(product['result'], ensure_ascii=False)}.
""".strip() for i, product in enumerate(examples)])


print(len(data_metrics))

## Загрузка параметров модели

load_dotenv(".env")

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
    return [
        {
            "examples": examples_str if examples_str else "Без примеров",
            "format_instructions": parser.get_format_instructions(),
            "problem_title": product["title"],
            COL_ATTRIBUTES: json.dumps(product[COL_ATTRIBUTES], ensure_ascii=False)        
        } for product in data_metrics
    ]

def postprocessing(result: List[Dict[str, Any]],
                   initial_dataset: List[Dict[str, Any]],
                   parser: PydanticOutputParser) -> List[Dict[str, Any]]:
    format_result = [[key for key in res.characteristics if key in product[COL_ATTRIBUTES]] 
                    for res, product in zip(parser.batch(result), initial_dataset)]
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
            format_result = postprocessing(result, batch, parser) # Получаем ключи, которы нужно оставить в характеристиках продукта
        except Exception as e:
            logger.error(f"Error in batch {i}: {e}")

        map_batch_id_to_result.append({
            'batch': batch,
            'result': format_result,
            'result_without_postprocessing': result
        })
        save_results(map_batch_id_to_result, f"{BASE_PATH_FOR_CORRECT_BATCH}/map_batch_id_to_result.json")

    return map_batch_id_to_result


class SimilarityListResponse(BaseModel):
    characteristics: List[str] = Field(..., description="Ответ на задачу")

parser = PydanticOutputParser(pydantic_object=SimilarityListResponse)

SYSTEM_PROMPT = """
Сопоставь название товарной позиции и ее характеристики. Отфильтруй те характеристики, которые явно упомянуты в названии.

Примеры:
{examples}

Следуй этим правилам:
- Характеристика должна **полностью или частично** иметь фрагмент строки в товарной позиции.
- Если значение не в виде булевой единицы, то ищи фрагмент или полное совпадение.
- Значение в характеристике и в товарной позиции **должно совпадать** полностью или частично и быть явно отнесено к ключу характеристики.
- Подтверждение соответствия должно быть явным.
- Ключ для ответа должен быть взят из характеристик.

Сопоставь каждую характеристику по пунктам в формате 'характеристика'-'фрагмент строки'.

Подумай шаг за шагом и напиши пояснения по каждой выбранной характеристике.
В конце сформируй только один ответ по данному формату: {format_instructions}.
""".strip()

USER_PROMPT = """
Товарная позиция: {problem_title}
Характеристики: {attributes}
""".strip()

prompt = create_model_prompts(SYSTEM_PROMPT, USER_PROMPT)

prepared_dataset = get_batch(data_metrics, examples_str, parser)

similarity_chain = prompt | llm | StrOutputParser()

map_batch_id_to_result = batched_processing(prepared_dataset, similarity_chain, parser)

logger.info(f"Обработка завершена")
