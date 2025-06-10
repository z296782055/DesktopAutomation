import base64
import json

import openai

from util import utils
api_key="MTcwZjMyOGItZGNmMi00YzJhLTgxZGItZDdjOWNkZGY4M2U4"
base_url="https://origin.nextway.top/v1/chat/completions"
# model = "gemini-2.5-pro-exp-03-25"
model = "gemini-2.5-flash-free"

client = openai.OpenAI(
        api_key=api_key,
        base_url=base_url
    )

with open("ai/" + utils.get_config("software") + "/text/index.txt", "rb") as text_file:
    index_text = text_file.read().decode('utf-8')

with open("ai/" + utils.get_config("software") + "/img/index.png", "rb") as img_file:
    index_img = img_file.read()
conversation = []
conversation.append({"role": "user", "content": index_text})
# conversation.append({"role": "user", "content": [
#                         {"type": "text", "text": index_text},
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/png;base64,{base64.b64encode(index_img).decode('utf-8')}",
#                                 "detail": "high"
#                             },
#                         },
#                     ]})
response = client.chat.completions.create(
    model=model,
    messages=conversation
)
assistant_response = response.choices[0].message.content
print(assistant_response)
conversation.append({"role": "assistant", "content": assistant_response})
with open("D:\\fk\\test\\20250608193615.png", "rb") as img_file:
    after_img = img_file.read()
with open("ai/" + utils.get_config("software") + "/text/after.txt", "rb") as text_file:
    after_text = text_file.read().decode('utf-8')
conversation.append({"role": "user", "content": [
                        {"type": "text", "text": after_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64.b64encode(after_img).decode('utf-8')}",
                                "detail": "high"
                            },
                        },
                    ]})
with open("D:\\fk\\test\\test.txt", 'w', encoding='utf-8') as f:
    json.dump(conversation, f, ensure_ascii=False, indent=4)
response = client.chat.completions.create(
    model=model,
    messages=conversation
)

print(assistant_response)