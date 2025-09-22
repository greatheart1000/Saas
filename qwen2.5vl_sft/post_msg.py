import requests

# 1. 请求地址
url = "http://127.0.0.1:8000/v1/chat/completions"

# 2. 请求头
headers = {
    "Content-Type": "application/json"
}

# 3. 请求体
payload = {
    "model": "gpt-4",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "你是汽车图像分类专家。请你生成这个图片对应的二级点位类型(point_type_name) 及其对应的三级点位名称(point_name)，最后，请仅输出一个有效 JSON，请开始你的推理过程"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://dcp-upload-pro.tos-accelerate.volces.com/2025-03-06/d1faed82-ae66-4029-a8df-ad3da9f81cce.jpg"
                    }
                }
            ]
        }
    ],
    "max_tokens": 300
}

# 4. 发送请求
response = requests.post(url, headers=headers, json=payload)

# 5. 处理响应
if response.status_code == 200:
    data = response.json()
    # 打印完整的返回结果
    print(data)
    # 或者只看第一个 choice 的内容
    # print(data["choices"][0]["message"]["content"])
else:
    print(f"请求失败，状态码：{response.status_code}")
    print(response.text)