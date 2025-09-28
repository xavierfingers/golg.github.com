# FastMCP Tools Server

This directory contains a `FastMCP` server with two custom tools: `list_files` and `nmap_scan`.

## Setup

1.  **Install `fastmcp`:**
    If you haven't already, install the `fastmcp` library:
    ```bash
    pip install fastmcp
    ```
2.  **Install Nmap:**
    Ensure Nmap is installed on your system. You can usually install it via your system's package manager (e.g., `sudo apt-get install nmap` on Debian/Ubuntu, `brew install nmap` on macOS).

## Running the Server

Navigate to this directory and run the `server.py` script:

```bash
cd /mnt/c/users/zaino/documents/networkchuck-site/fastmcp_tools_server
python server.py
```

The server will start and listen on the default `FastMCP` port (usually `http://127.0.0.1:8000`).

## Using the Tools

You can interact with the tools using a `FastMCP` client or by sending HTTP requests.

### 1. `list_files` Tool

This tool lists files and directories in a specified path.

**Example Usage (Python client):**

```python
from fastmcp import FastMCPClient

client = FastMCPClient("http://127.0.0.1:8000")

# List files in the current directory
print(client.list_files())

# List files in a specific directory (e.g., 'content/posts')
print(client.list_files(path="content/posts"))
```

### 2. `nmap_scan` Tool

This tool performs an Nmap scan on a given target with specified options.

**WARNING: Security Implications**
Exposing Nmap functionality through a server can have significant security implications. Nmap is a powerful network scanning tool that can be used for reconnaissance and vulnerability assessment. **Use this tool responsibly and ensure you understand and mitigate the risks if you deploy this in a production environment.**

**Example Usage (Python client):**

```python
from fastmcp import FastMCPClient

client = FastMCPClient("http://127.0.0.1:8000")

# Perform a fast scan on localhost
print(client.nmap_scan(target="127.0.0.1", options="-F"))

# Perform a more comprehensive scan (example, adjust options as needed)
# print(client.nmap_scan(target="scanme.nmap.org", options="-sV -p 80,443"))
```
