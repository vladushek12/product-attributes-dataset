from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate
)

from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.output_parsers.json import SimpleJsonOutputParser

from dotenv import load_dotenv

import os
import json
from typing import List

with open("./metrics.json", "r", encoding="utf-8") as file:
    data_metrics = json.load(file)

print(len(data_metrics))

## Загрузка параметров модели

load_dotenv(".env")

model_params = {
    "base_url": os.getenv("OPENAI_BASE_URL"),
    "model_name": os.getenv("OPENAI_MODEL_NAME"),
    "api_key": os.getenv("OPENAI_API_KEY"),
    "temperature": 0
}

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
            "problem_decomposition": json.dumps(product["decomposition"], ensure_ascii=False)        
        } for product in data_metrics
    ]

def get_similarity_results(prompt, 
                           llm,
                           batch, 
                           parser = SimpleJsonOutputParser()):
    similarity_chain = prompt | llm | parser

    return similarity_chain.batch(batch)

def evaluate_predictions(y_true, y_pred):
    y_true = set(y_true)
    y_pred = set(y_pred)
    
    TP = len(y_true & y_pred)  # Совпадающие элементы (правильные предсказания)
    FP = len(y_pred - y_true)  # Ошибочные предсказания (лишние элементы)
    FN = len(y_true - y_pred)  # Пропущенные правильные элементы
    TN = None  # Не учитывается в таких задачах
    
    return TP, FP, FN

def evaluate_batch_predictions(batch_results: List[int]):# -> dict[str, Any]:
    total_TP, total_FP, total_FN = 0, 0, 0
    
    for TP, FP, FN in batch_results:
        total_TP += TP
        total_FP += FP
        total_FN += FN
    
    precision = total_TP / (total_TP + total_FP) if (total_TP + total_FP) > 0 else 0
    recall = total_TP / (total_TP + total_FN) if (total_TP + total_FN) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    total_correct = sum([1 for _, FP, FN in batch_results if FP == 0 and FN == 0])
    
    return {
        "TP": total_TP,
        "FP": total_FP,
        "FN": total_FN,
        "Precision": precision,
        "Recall": recall,
        "F1-score": f1,
        "total_correct": total_correct
    }

with open("./examples.json", "r", encoding="UTF-8") as file:
    examples = json.load(file)

examples_str = "\n".join([f"""
{i+1})Название товара: {product["title"]}.
Характеристики: {json.dumps(product['attributes'], ensure_ascii=False)}.
Ответ: {json.dumps(product['result'], ensure_ascii=False)}.
""".strip() for i, product in enumerate(examples)])

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
Характеристики: {problem_decomposition}
""".strip()

prompt = create_model_prompts(SYSTEM_PROMPT, USER_PROMPT)

batch = [{
    "examples": examples_str,
    "format_instructions": parser.get_format_instructions(),
    "problem_title": product["title"],
    "problem_decomposition": json.dumps(product["decomposition"], ensure_ascii=False)
} for product in data_metrics]

similarity_chain = prompt | llm

result_batch = similarity_chain.batch(batch)

format_result = [[key for key in res.characteristics if key in product["decomposition"]] 
                    for res, product in zip(parser.batch(result_batch), data_metrics)]

y_true_arr = [product["correct_ans"] for product in data_metrics]
y_pred_arr = format_result

scores = [evaluate_predictions(y_true, y_pred) for y_true, y_pred in zip(y_true_arr, y_pred_arr)]

dump_data = [{
    "product": product,
    "reasoning": res.content,
    "format_result": format,
    "score": score
} for product, res, format, score in zip(data_metrics, result_batch, format_result, scores)]

with open("internal_result.json", "w", encoding="utf-8") as file:
    json.dump(dump_data, file, ensure_ascii=False)

with open("scores.json", "w", encoding="UTF-8") as file:
    json.dump(evaluate_batch_predictions(scores), file, ensure_ascii=False)
