from openai import OpenAI
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

api_key = ""
client = OpenAI(api_key=api_key)
text1 = ""
text2 = ""

# 构建原始消息，包含变量 text_fragment
original_message = "" + text2

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": original_message}
    ]
)

text3 = response.choices[0].message.content

# 使用正则表达式保留汉字
text3 = re.sub(r'[^\u4e00-\u9fff]', '', text3)
print("隐写的文本是："+text1)
print("隐写后直接提取的文本是："+text2)
print("经过NLP处理后的文本是："+text3)
print("经过NLP处理后添加符号后的文本是："+response.choices[0].message.content)


def chinese_tokenizer(text):
    return jieba.lcut(text)
# 分词
text1_cut = " ".join(chinese_tokenizer(text1))
text2_cut = " ".join(chinese_tokenizer(text2))
text3_cut = " ".join(chinese_tokenizer(text3))

# 初始化 TF-IDF 向量化器，使用自定义分词器
vectorizer = TfidfVectorizer(tokenizer=chinese_tokenizer)

# 将文本转换为向量
vectors = vectorizer.fit_transform([text1_cut, text2_cut, text3_cut])

# 计算相似度
similarity_12 = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
similarity_13 = cosine_similarity(vectors[0:1], vectors[2:3])[0][0]

print("隐写前文本与直接提取后文本的相似度:", similarity_12, end="\n")
print("隐写前文本与经过NLP处理后的提取文本的相似度:", similarity_13, end="\n")