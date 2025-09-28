
import asyncio
from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport

async def main():
    # Connect to the server using the default STDIO transport
    transport = PythonStdioTransport(
        "mcp_server.py",
        env={"PYTHONPATH": "/usr/lib/python3/dist-packages"}
    )
    async with Client(transport) as client:
        # Call the 'hello' tool with the name 'World'
        result = await client.call_tool("hello", {"name": "World"})
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
