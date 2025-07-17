# mcp_client_demo.py
import asyncio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

class WeatherMCPClient:
    def __init__(self, server_url="http://127.0.0.1:1234/sse"):
        self.server_url = server_url
        self._sse_context = None
        self._session = None

    async def __aenter__(self):
        # 創建 SSE 通道
        self._sse_context = sse_client(self.server_url)
        self.read, self.write = await self._sse_context.__aenter__()

        # 創建 MCP 會話
        self._session = ClientSession(self.read, self.write)
        await self._session.__aenter__()
        await self._session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
        if self._sse_context:
            await self._sse_context.__aexit__(exc_type, exc_val, exc_tb)

    async def list_tools(self):
        return await self._session.list_tools()

    async def list_resources(self):
        return await self._session.list_resources()

    async def call_tool(self, name, arguments):
        return await self._session.call_tool(name, arguments)


async def main():
    async with WeatherMCPClient() as client:
        print("✅ 成功連接 MCP Server")

        tools = await client.list_tools()

        print("\n🛠 可用工具:")
        print(tools)

        resources = await client.list_resources()
        print("\n📚 可用資源:")
        print(resources)

        print("\n📡 呼叫 WeatherTool 工具(city=Taipei)...")
        city = input("請輸入要查詢天氣的城市：")
        result = await client.call_tool("get_weather", {"city": city})

        print("\n🎯 工具返回:")
        for item in result.content:
            print(" -", item.text)

if __name__ == "__main__":
    asyncio.run(main())