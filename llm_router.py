# llm_router.py
import json
import requests

# Ollama 配置
OLLAMA_API_URL = "BASE_URL"

class OllamaLLM:
    """
    自訂 LLM 類，使用 Ollama API 來生成回覆
    """
    def __init__(self, model: str = "MODEL_NAME"):
        self.model = model

    def generate(self, messages):
        """
        發送對話訊息給 Ollama API 並返回 LLM 的回覆文字

        參數:
            messages: 一個 list，每個元素都是形如 {'role': role, 'content': content} 的字典

        返回:
            LLM 返回的回覆文字
        """
        request_body = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        #print(f"發送請求到 Ollama API: {json.dumps(request_body, ensure_ascii=False)}")

        response = requests.post(
            OLLAMA_API_URL,
            json=request_body
        )

        if response.status_code != 200:
            print(f"Ollama API 錯誤: {response.status_code}")
            print(f"錯誤詳情: {response.text}")
            raise Exception(f"Ollama API 返回錯誤: {response.status_code}")
        
        #resp_text = response.text
        #print("原始回應（未解析）：", repr(resp_text))
        try:
            response_json = response.json()
            #print(f"Ollama API 回應: {json.dumps(response_json, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print("無法解析 Ollama API 回應為 JSON，請檢查回應格式")
            raise Exception("Ollama API 回應格式錯誤")

        # 提取 LLM 回應文字
        try:
            content = response_json['message']['content']
            return content
        except KeyError:
            raise Exception("無法從 Ollama 回應中提取內容")


if __name__ == "__main__":
    # 範例系統提示和使用者輸入
    messages = [
        {"role": "system", "content": "你是一個智慧助理，可以協助查詢天氣資訊。"},
        {"role": "user", "content": "請告訴我台北今天的天氣狀況。"}
    ]

    llm = OllamaLLM()
    try:
        result = llm.generate(messages)
        print("LLM 返回結果:")
        print(result)
    except Exception as e:
        print(f"呼叫 Ollama 時發生例外: {e}")
