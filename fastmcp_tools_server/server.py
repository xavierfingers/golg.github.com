import os
import subprocess
from fastmcp import FastMCP

# Create a new MCP server instance
server = FastMCP()

@server.tool()
def list_files(path: str = ".") -> dict:
    """
    Lists files and directories in the specified path.
    By default, lists contents of the current directory.
    """
    try:
        # Ensure the path is within a reasonable boundary or project directory
        # For security, you might want to add more robust path validation
        # to prevent access to arbitrary system directories.
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(os.getcwd(), path))

        if not os.path.exists(path):
            return {"error": f"Path not found: {path}"}
        if not os.path.isdir(path):
            return {"error": f"Path is not a directory: {path}"}

        contents = os.listdir(path)
        files = [item for item in contents if os.path.isfile(os.path.join(path, item))]
        directories = [item for item in contents if os.path.isdir(os.path.join(path, item))]
        return {"path": path, "files": files, "directories": directories}
    except Exception as e:
        return {"error": str(e)}

@server.tool()
def nmap_scan(target: str, options: str = "-F") -> dict:
    """
    Performs an Nmap scan on the specified target with given options.
    WARNING: Running Nmap can have security implications. Use responsibly.
    Requires Nmap to be installed on the system.
    Default options: -F (fast scan)
    """
    try:
        # Basic validation to prevent command injection, but not exhaustive.
        # For production, consider a whitelist of allowed Nmap options.
        if not target:
            return {"error": "Nmap target cannot be empty."}

        # Construct the Nmap command
        command = ["nmap"] + options.split() + [target]

        # Execute the command
        process = subprocess.run(command, capture_output=True, text=True, check=True)

        return {
            "command": " ".join(command),
            "stdout": process.stdout,
            "stderr": process.stderr,
            "returncode": process.returncode
        }
    except subprocess.CalledProcessError as e:
        return {
            "error": "Nmap command failed",
            "command": " ".join(e.cmd),
            "stdout": e.stdout,
            "stderr": e.stderr,
            "returncode": e.returncode
        }
    except FileNotFoundError:
        return {"error": "Nmap command not found. Please ensure Nmap is installed and in your PATH."}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("Starting FastMCP server with 'list_files' and 'nmap_scan' tools...")
    print("Access the server at http://127.0.0.1:8000 (default FastMCP port)")
    print("WARNING: The 'nmap_scan' tool can have significant security implications. Use with caution.")
    server.run()
