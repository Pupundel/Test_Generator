import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def fetch_ai_question_gemini(topic, complexity, q_type, pdf_bytes=None, exclude_list=None):
    instruction = (
        f"Ты — строгий составитель тестов. Твоя задача: создать ОДИН вопрос на тему: '{topic}'.\n"
        f"Сложность: {complexity}. Тип вопроса: {q_type}.\n\n"
        "ПРАВИЛА:\n"
        "1. Используй СТРОГО информацию из предоставленного документа (если он есть).\n"
        "2. НЕ ПРИДУМЫВАЙ ничего сам. Не используй свои знания вне рамок документа.\n"
        "3. Не выходи за границы содержания файла.\n"
        "4. Если документа нет, опирайся только на общеизвестные факты по теме.\n"
    )

    if exclude_list and len(exclude_list) > 0:
        avoid = "\n".join([f"- {q}" for q in exclude_list])
        instruction += f"\n5. НОВЫЙ ВОПРОС НЕ ДОЛЖЕН повторять эти (даже по смыслу):\n{avoid}"

    parts = [types.Part.from_text(text=instruction)]

    if pdf_bytes:
        parts.insert(
            0,
            types.Part.from_bytes(
                data=pdf_bytes,
                mime_type="application/pdf"
            )
        )

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=parts
    )

    return response.text.strip()

def fetch_ai_answers_gemini(question_text):
    prompt = (
        f"Для вопроса '{question_text}' придумай 4 варианта ответа.\n"
        "Один вариант должен быть ТОЧНО верным согласно документу, остальные три — убедительными, но ложными.\n"
        "Верни ответ СТРОГО в формате JSON списка объектов. Пример:\n"
        '[{"text": "ответ1", "is_correct": true}, {"text": "ответ2", "is_correct": false}, ...]'
    )
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)