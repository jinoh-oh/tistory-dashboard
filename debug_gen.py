import google.generativeai as genai
import config
import json
import os

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

topic = "혈액검사"
prompt = f"당신은 블로그 전문가입니다. {topic}에 대해 1600자 이상으로 작성하세요. JSON 형식으로 답하세요: {{'title': '...', 'content': '...', 'tags': []}}"

try:
    print(f"Using API Key: {config.GEMINI_API_KEY[:5]}...")
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    print("Response received!")
    print(response.text[:200])
except Exception as e:
    print(f"ERROR: {e}")
    try:
        # Check if response has something even on error
        print(f"Raw Response: {response}")
    except NameError:
        pass
