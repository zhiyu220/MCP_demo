import asyncio
import json
import re
from llm_router import OllamaLLM
from mcp_client_demo import WeatherMCPClient


def extract_json_from_reply(reply: str):
    """
    提取 LLM 返回的 JSON 內容，自動處理 markdown 包裹、多餘引號、巢狀等。
    支援 string 或 dict 格式。
    如果無法解出 dict，則返回原始 string。
    """
    # 如果已經是 dict，直接返回
    if isinstance(reply, dict):
        return reply

    # 清除 markdown ```json ``` 包裹
    if isinstance(reply, str):
        reply = re.sub(r"^```(?:json)?|```$", "", reply.strip(), flags=re.IGNORECASE).strip()

    # 最多嘗試 3 層 json.loads 解碼
    for _ in range(3):
        try:
            parsed = json.loads(reply)
            if isinstance(parsed, dict):
                return parsed
            else:
                reply = parsed  # 如果解出來還是 str，繼續下一層
        except Exception:
            break

    # 如果最終不是 dict，返回原始字串（表示是普通答覆）
    return reply


llm = OllamaLLM()


async def main():
    # === 初始化 MCP 客戶端 ===
    client = WeatherMCPClient()
    await client.__aenter__()

    tools = await client.list_tools()
    resources = await client.list_resources()
    tool_names = [t.name for t in tools.tools]

    tool_descriptions = "\n".join(f"- {t.name}: {t.description}" for t in tools.tools)
    resource_descriptions = "\n".join(f"- {r.uri}" for r in resources.resources)

    system_prompt = (
            "你是一個智慧助理，擁有以下工具和資源可以呼叫：\n\n"
            f"🛠 工具列表：\n{tool_descriptions or '（無）'}\n\n"
            f"📚 資源列表：\n{resource_descriptions or '（無）'}\n\n"
            "請優先呼叫可用的Tool或Resource，而不是llm內部生成。僅根據上下文呼叫工具，不傳入不需要的參數進行呼叫\n"
            "如果需要，請以 JSON 返回 tool_calls，格式如下：\n"
            '{"tool_calls": [{"name": "get_weather_now", "arguments": {"city": "Taipei"}}]}\n'
            '城市名稱請先轉為英文再做查詢，若要回答溫度，請四捨五入到整數位\n'
            '如已回答完成，無需呼叫工具，返回：{"tool_calls": null}'
        )

    # === 構造 LLM 上下文訊息 ===
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    while True:
        # === Step 1. 使用者 → MCP主機：提出問題 ===
        user_input = input("\n請輸入你的問題（輸入 exit 退出）：\n> ")
        if user_input.lower() in ("exit", "退出"):
            break
        messages.append({"role": "user", "content": user_input})       

        final_reply = ""

        # === 循環處理 tool_calls，直到 LLM 給出最終 content 為止 ===
        while True:
            # === Step 2. MCP主機 → LLM：轉發上下文 ===
            reply = llm.generate(messages)
            print(f"\n🤖 LLM 回覆：\n{reply}")

            # === Step 3. 解析 JSON 格式回覆（或普通字串） ===
            parsed = extract_json_from_reply(reply)

            # === 如果是普通自然語言字串，說明 LLM 已直接答覆使用者 ===
            if isinstance(parsed, str):
                final_reply = parsed
                messages.append({"role": "assistant", "content": final_reply})
                break

            # === 如果是字典，判斷是否包含工具呼叫 ===
            tool_calls = parsed.get("tool_calls")
            if not tool_calls:
                # LLM 給出普通答覆結構（帶 content 欄位）
                final_reply = parsed.get("content", "")
                messages.append({"role": "assistant", "content": final_reply})
                break

            # === 遍歷 LLM 請求的工具呼叫列表 ===
            for tool_call in tool_calls:
                # === Step 4. LLM → MCP客戶端：請求使用工具 ===
                tool_name = tool_call["name"]
                arguments = tool_call["arguments"]

                if tool_name not in tool_names:
                    raise ValueError(f"❌ 工具 {tool_name} 未註冊")

                # === Step 5. MCP客戶端 → MCP伺服器：呼叫工具 ===
                #print(f"🛠 呼叫工具 {tool_name} ")
                result = await client.call_tool(tool_name, arguments)

                # === Step 8. MCP伺服器 → MCP客戶端：返回結果 ===
                tool_output = result.content[0].text
                #print(f"📦 工具 {tool_name} ")

                # === Step 9. MCP客戶端 → LLM：提供工具結果 ===
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": tool_output
                })

            # Step 10: 再次呼叫 LLM，進入下一輪（可能再次產生 tool_calls）

        # === Step 11. MCP主機 → 使用者：最終結果答覆 ===
        print(f"\n🎯 最終答覆：{final_reply}")

    await client.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(main())