#!/usr/bin/env python3
# client.py
import socket, sys

SERVER1_IP = "172.31.16.124"  # <-- PUT SERVER1 PRIVATE IP HERE
SERVER1_PORT = 5001
filename = sys.argv[1] if len(sys.argv) > 1 else "file1.txt"

def recv_line(conn):
    buf = bytearray()
    while True:
        b = conn.recv(1)
        if not b:
            break
        buf += b
        if buf.endswith(b"\n"):
            break
    return bytes(buf).decode(errors="replace").rstrip("\n")

def recv_exact(conn, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed while reading body")
        buf += chunk
    return bytes(buf)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((SERVER1_IP, SERVER1_PORT))
    s.sendall(f"GET {filename}\n".encode())

    header = recv_line(s)  # e.g., OK ONE <len> / OK BOTH <l1> <l2> / ERROR NOTFOUND
    parts = header.split()
    if parts[:2] == ["OK", "ONE"]:
        length = int(parts[2]); data = recv_exact(s, length)
        print("[CLIENT] Received ONE copy:")
        print(data.decode(errors="ignore"))
        # Optionally save:
        # open("out_one.txt","wb").write(data)
    elif parts[:2] == ["OK", "BOTH"]:
        l1, l2 = int(parts[2]), int(parts[3])
        d1 = recv_exact(s, l1); d2 = recv_exact(s, l2)
        print("[CLIENT] Received BOTH copies:")
        print("\n--- SERVER1 version ---\n", d1.decode(errors="ignore"))
        print("\n--- SERVER2 version ---\n", d2.decode(errors="ignore"))
        # Optionally save:
        # open("out_server1.txt","wb").write(d1)
        # open("out_server2.txt","wb").write(d2)
    else:
        print("[CLIENT]", header)

