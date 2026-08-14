#!/usr/bin/env python3
import sys
import os
import json
import socket
import struct
import argparse

HEADER_STRUCT = struct.Struct(">I")

def run_code_in_qgis(code, host="127.0.0.1", port=9876):
    command = {
        "type": "execute_code",
        "params": {
            "code": code
        }
    }
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.settimeout(60.0)
    
    try:
        s.connect((host, port))
        
        payload = json.dumps(command).encode("utf-8")
        header = HEADER_STRUCT.pack(len(payload))
        s.sendall(header)
        s.sendall(payload)
        
        resp_len_header = b""
        while len(resp_len_header) < 4:
            chunk = s.recv(4 - len(resp_len_header))
            if not chunk:
                raise ConnectionError("Failed to read length header from server")
            resp_len_header += chunk
            
        resp_len = HEADER_STRUCT.unpack(resp_len_header)[0]
        
        chunks = []
        bytes_recvd = 0
        while bytes_recvd < resp_len:
            chunk = s.recv(min(resp_len - bytes_recvd, 65536))
            if not chunk:
                raise ConnectionError("Connection closed before reading full response")
            chunks.append(chunk)
            bytes_recvd += len(chunk)
            
        resp_payload = b"".join(chunks).decode("utf-8")
        return json.loads(resp_payload)
    except ConnectionRefusedError:
        print(f"[ERROR] Could not connect to QGIS on {host}:{port}. Is QGIS running and the MCP plugin enabled?", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Execution failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        s.close()

def main():
    parser = argparse.ArgumentParser(description="Run PyQGIS python scripts inside a running QGIS instance.")
    parser.add_argument("script_path", help="Path to the python script to run in QGIS.")
    parser.add_argument("--host", default="127.0.0.1", help="TCP Host of the QGIS instance.")
    parser.add_argument("--port", type=int, default=9876, help="TCP Port of the QGIS instance.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.script_path):
        print(f"[ERROR] Script file not found: {args.script_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(args.script_path, "r", encoding="utf-8") as f:
        code_str = f.read()
        
    print(f"Sending {args.script_path} to QGIS at {args.host}:{args.port}...")
    response = run_code_in_qgis(code_str, args.host, args.port)
    
    if response.get("status") == "success":
        res = response.get("result", {})
        if res.get("executed"):
            print("\n--- stdout ---")
            print(res.get("stdout"))
            if res.get("stderr"):
                print("\n--- stderr ---")
                print(res.get("stderr"))
            print("----------------")
            print("PyQGIS execution completed successfully!")
        else:
            print("\n[ERROR] Script failed execution inside QGIS:", file=sys.stderr)
            print(res.get("error"), file=sys.stderr)
            print("\nTraceback:", file=sys.stderr)
            print(res.get("traceback"), file=sys.stderr)
            sys.exit(1)
    else:
        print(f"[ERROR] MCP Server returned error: {response.get('message')}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
