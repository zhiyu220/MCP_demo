#mcp_server_demo.py
from mcp.server.fastmcp import FastMCP
import asyncio
import requests
from datetime import datetime

mcp = FastMCP(name="weather-demo", host="0.0.0.0", port=1234)

@mcp.tool(name="get_weather_now", description="獲取指定城市現在的天氣資訊")
async def get_weather_now(city: str) -> str:
    """取得指定城市的天氣資料"""
    try:
        API_KEY = "OPENWEATHER_API_KEY" 
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": API_KEY, "units": "metric", "lang": "zh_tw"}
        )
        weather = resp.json()
        if resp.status_code == 200:
            # 取主要天氣描述
            description = weather['weather'][0]['description']
            temp = weather['main']['temp']
            return f"{city}天氣：{description}，溫度：{temp}°C"
        else:
            return f"無法取得天氣資料: {weather.get('message', '未知錯誤')}"
    except Exception as e:
        return f"天氣API調用失敗: {str(e)}"

@mcp.tool(name="get_weather_forcast_4days", description="獲取指定城市的近期天氣預報資訊")
async def get_weather_forcast_4days(city: str) -> str:
    """取得指定城市的天氣預報資料（未來4天，每3小時一次）"""
    try:
        API_KEY = "OPENWEATHER_API_KEY"
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"q": city, "appid": API_KEY, "units": "metric", "lang": "zh_tw"}
        )
        weather = resp.json()
        if resp.status_code == 200 and "list" in weather:
            result = [f"{city}未來4天天氣預報："]
            # 只取前32筆（4天，每3小時一次，共32筆）
            for item in weather["list"][:32]:
                dt_txt = item.get("dt_txt", "")
                description = item["weather"][0]["description"]
                temp = item["main"]["temp"]
                result.append(f"{dt_txt}: {description}，溫度：{temp}°C")
            return "\n".join(result)
        else:
            return f"無法取得天氣資料: {weather.get('message', '未知錯誤')}"
    except Exception as e:
        return f"天氣API調用失敗: {str(e)}"

@mcp.tool(name="get_weather_forcast_1month", description="獲取指定城市的本月天氣預報資訊")
async def get_weather_forcast_1month(city: str) -> str:
    """取得指定城市的天氣預報資料（本月每日預報）"""
    try:
        API_KEY = "OPENWEATHER_API_KEY"
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast/climate",
            params={"q": city, "appid": API_KEY, "units": "metric", "lang": "zh_tw"}
        )
        weather = resp.json()
        if resp.status_code == 200 and "list" in weather:
            result = [f"{city}本月每日天氣預報："]
            for item in weather["list"]:
                # 轉換日期
                dt = datetime.utcfromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                description = item["weather"][0]["description"]
                temp_day = item["temp"]["day"]
                temp_min = item["temp"]["min"]
                temp_max = item["temp"]["max"]
                result.append(f"{dt}: {description}，白天溫度：{temp_day}°C，最低：{temp_min}°C，最高：{temp_max}°C")
            return "\n".join(result)
        else:
            return f"無法取得天氣資料: {weather.get('message', '未知錯誤')}"
    except Exception as e:
        return f"天氣API調用失敗: {str(e)}"
    

async def main():
    print("✅ 啟動 MCP Server: http://127.0.0.1:1234")
    await mcp.run_sse_async()

if __name__ == "__main__":
    asyncio.run(main())