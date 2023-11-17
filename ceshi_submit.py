
from openai import OpenAI

api_key = ""
client = OpenAI(api_key=api_key)

response = client.files.create(
  file=open("/Users/limingyang/Downloads/mydata.jsonl", "rb"),
  purpose="fine-tune"
)
print(response)