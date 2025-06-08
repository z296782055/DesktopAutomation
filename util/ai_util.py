import base64
import logging

import openai
from util import utils

api_key = ""
api_base = "https://origin.nextway.top/v1/chat/completions"
model = "gemini-2.5-flash-free"


def simple_chat():
    client = openai.OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    conversation = []
    text_path = "./ai/"+utils.get_config("software")+"/text/index.txt"
    image_path = "./ai/"+utils.get_config("software")+"/img/index.png"
    with open(text_path, "r", encoding='utf-8') as text_file:
        text = text_file.read()
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    conversation.append({"role": "user", "content": [
        {"type": "text", "text": text},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
                "detail": "high"
            },
        },
    ]})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=conversation
        )
        assistant_response = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": assistant_response})
        print(f"助手: {assistant_response}")
    except Exception as e:
        logging.exception(e)

