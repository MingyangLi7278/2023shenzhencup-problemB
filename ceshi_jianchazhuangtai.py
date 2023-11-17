from openai import OpenAI

api_key = ""
client = OpenAI(api_key=api_key)

job_status = client.fine_tuning.jobs.retrieve('')
print(job_status)
