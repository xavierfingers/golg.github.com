
from fastmcp import FastMCP

# Create a new MCP server
server = FastMCP()

@server.tool()
def hello(name: str) -> str:
    """
    A simple tool that returns a greeting.
    """
    return f"Hello, {name}!"

if __name__ == "__main__":
    server.run()
