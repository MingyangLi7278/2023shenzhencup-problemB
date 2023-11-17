from openai import OpenAI

api_key = ""
client = OpenAI(api_key=api_key)

fine_tune_response = client.fine_tuning.jobs.create(
  training_file="",
  model="gpt-3.5-turbo"
)

print(fine_tune_response)
