
from fastmcp import FastMCP

# Create a new MCP server
server = FastMCP()

@server.tool()
def howdy(name: str) -> str:
    """
    A simple tool that returns a Texas-style greeting.
    """
    return f"Howdy, {name}!"

if __name__ == "__main__":
    server.run()
