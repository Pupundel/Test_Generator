import os
import json
import PyPDF2
import io
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def fetch_ai_question_gemini(topic, complexity, q_type, pdf_bytes=None):
    context_text = ""
    if pdf_bytes:
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    context_text += text + "\n"
            context_text = context_text[:8000]  # Ограничим объем для скорости
        except:
            context_text = "Ошибка чтения PDF"

    # 2. Формируем промпт
    source = f"на основе текста: {context_text}" if context_text else f"на тему: {topic}"
    prompt = f"Составь один {complexity} {q_type} вопрос {source}. Пиши ТОЛЬКО текст вопроса."

    # 3. Запрос
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Ты методист. Генерируешь только текст вопроса."},
            {"role": "user", "content": prompt}
        ],
        stream=False
    )
    return response.choices[0].message.content.strip()


def fetch_ai_answers_gemini(question_text):
    prompt = f"Для вопроса '{question_text}' придумай 4 варианта ответа (один верный). Верни ТОЛЬКО JSON список объектов: [{{'text': '...', 'is_correct': true}}, ...]"

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Ты выдаешь только чистый JSON."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()
    # Очистка от Markdown разметки
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    return json.loads(content)