"""
Minimal Gemini MCP-style server for Gemini clients (gemini://) that provides:
 - directory listing ("lit dirs")
 - simple Nmap scan endpoint (runs nmap locally and returns results)
 - a couple of utility endpoints

SECURITY WARNING
- This server can run arbitrary nmap scans on targets. Only scan hosts/networks
  you own or are explicitly authorized to scan. Misuse may be illegal.
- By default the script REQUIRES you to list allowed targets or CIDR ranges in
  ALLOWED_TARGETS. Do NOT run with a permissive whitelist on production networks.

USAGE
1) Generate a TLS cert/key (self-signed for testing):
   openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out cert.pem

2) Run (needs Python 3.8+ and nmap installed on the system):
   python gemini_mcp_server.py --cert cert.pem --key key.pem --host 0.0.0.0 --port 1965

3) Examples of requests (using a gemini client):
   gemini://yourhost:1965/list?path=/home/user
   gemini://yourhost:1965/nmap?target=127.0.0.1

This script is intentionally small and synchronous for clarity. Extend with
authorization, rate limiting and sandboxing as required for real deployments.
"""

import argparse
import asyncio
import ssl
import urllib.parse
import os
import shlex
import json
import subprocess
from ipaddress import ip_network, ip_address

# --- Configuration: edit before running ---
ALLOWED_TARGETS = [
    "127.0.0.1/32",
    "::1/128",
    # Add CIDR ranges you trust, e.g. "192.168.1.0/24"
]
# Maximum bytes of nmap output to return (protects server memory)
NMAP_OUTPUT_LIMIT = 200_000  # bytes
# Timeout for subprocess invocations
SUBPROCESS_TIMEOUT = 30  # seconds
# ----------------------------------------

# Pre-parse allowed networks
ALLOWED_NETWORKS = [ip_network(x) for x in ALLOWED_TARGETS]

GEMINI_OK = "20"  # success
GEMINI_BAD_REQUEST = "59"  # temporary failure (used for errors)

async def handle_gemini(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        # Read request line (single line, terminated by \r\n), max 8192 bytes
        data = await reader.readuntil(b"\r\n")
    except Exception:
        writer.close()
        await writer.wait_closed()
        return

    req_line = data.decode('utf-8', errors='replace').strip()
    # The gemini request line is the URL
    url = req_line
    parsed = urllib.parse.urlparse(url)

    # Only support gemini scheme or plain path requests
    path = parsed.path or "/"
    query = urllib.parse.parse_qs(parsed.query)

    addr = writer.get_extra_info('peername')
    print(f"Request from {addr}: {url}")

    # Simple routing
    try:
        if path.startswith('/list'):
            # /list?path=/some/dir
            target = query.get('path', [None])[0]
            body = handle_list(target)
            await send_gemini_response(writer, GEMINI_OK, "text/plain; charset=utf-8", body)

        elif path.startswith('/nmap'):
            # /nmap?target=1.2.3.4
            target = query.get('target', [None])[0]
            body = await handle_nmap(target)
            await send_gemini_response(writer, GEMINI_OK, "text/plain; charset=utf-8", body)

        elif path.startswith('/info'):
            body = json.dumps({
                'server': 'gemini-mcp-example',
                'features': ['list', 'nmap']
            }, indent=2)
            await send_gemini_response(writer, GEMINI_OK, "application/json; charset=utf-8", body)

        else:
            body = 'Unknown endpoint. Available: /list, /nmap, /info\n'
            await send_gemini_response(writer, GEMINI_BAD_REQUEST, "text/plain; charset=utf-8", body)

    except Exception as e:
        err = f"Error handling request: {e}\n"
        await send_gemini_response(writer, GEMINI_BAD_REQUEST, "text/plain; charset=utf-8", err)

    writer.close()
    await writer.wait_closed()

async def send_gemini_response(writer, status_code, meta, body: str):
    # Gemini response: status SP meta CRLF body
    header = f"{status_code} {meta}\r\n".encode('utf-8')
    writer.write(header)
    if body:
        writer.write(body.encode('utf-8'))
    await writer.drain()

def handle_list(path: str) -> str:
    if not path:
        return 'No path provided. Use /list?path=/some/dir\n'
    # Prevent directory traversal beyond allowed root(s) if desired.
    if not os.path.exists(path):
        return f'Path not found: {path}\n'
    if not os.path.isdir(path):
        return f'Not a directory: {path}\n'

    entries = []
    try:
        with os.scandir(path) as it:
            for e in it:
                typ = 'DIR' if e.is_dir() else 'FILE'
                size = e.stat().st_size if e.is_file() else ''
                entries.append(f"{typ:4}  {e.name}  {size}")
    except PermissionError:
        return f'Permission denied: {path}\n'

    return "\n".join(entries) + "\n"

def is_target_allowed(target: str) -> bool:
    # Basic validation: must be an IP (v4 or v6)
    try:
        ip = ip_address(target)
    except Exception:
        return False
    for net in ALLOWED_NETWORKS:
        if ip in net:
            return True
    return False

async def handle_nmap(target: str) -> str:
    if not target:
        return 'No target specified. Use /nmap?target=1.2.3.4\n'

    # Validate target is allowed
    if not is_target_allowed(target):
        return f'Target not allowed: {target}\n'

    # Build nmap command carefully (avoid shell=True)
    cmd = ['nmap', '-sV', '--reason', target]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=SUBPROCESS_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            return f'nmap timed out after {SUBPROCESS_TIMEOUT} seconds\n'

        out = stdout[:NMAP_OUTPUT_LIMIT].decode('utf-8', errors='replace')
        if len(stdout) > NMAP_OUTPUT_LIMIT:
            out += '\n---output truncated---\n'
        if stderr:
            out += '\n[nmap stderr]\n' + stderr.decode('utf-8', errors='replace')
        return out

    except FileNotFoundError:
        return 'nmap not installed on server. Install nmap to enable scan.\n'
    except Exception as e:
        return f'Failed to run nmap: {e}\n'

async def main(args):
    sslctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    sslctx.load_cert_chain(args.cert, args.key)

    server = await asyncio.start_server(handle_gemini, host=args.host, port=args.port, ssl=sslctx)

    addr = server.sockets[0].getsockname()
    print(f'Gemini MCP server listening on {addr}')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Minimal Gemini MCP server (list, nmap)')
    parser.add_argument('--cert', required=True, help='Path to TLS certificate (PEM)')
    parser.add_argument('--key', required=True, help='Path to TLS private key (PEM)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind')
    parser.add_argument('--port', type=int, default=1965, help='Port to bind (Gemini default 1965)')
    args = parser.parse_args()

    # Quick check: ensure ALLOWED_TARGETS parsed
    print('Allowed target networks:', ALLOWED_TARGETS)

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print('\nShutting down')
