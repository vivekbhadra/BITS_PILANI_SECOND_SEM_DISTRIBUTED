#!/usr/bin/env python3
import socket, os

HOST = "0.0.0.0"
PORT = 5002
ROOT = os.path.expanduser("~/file_storage")

def recv_line(conn):
    buf = bytearray()
    while True:
        b = conn.recv(1)
        if not b: break
        buf += b
        if buf.endswith(b"\n"): break
    return bytes(buf).decode(errors="replace").rstrip("\n")

def send_found(conn, data: bytes):
    header = f"FOUND {len(data)}\n".encode()
    conn.sendall(header + data)

def send_notfound(conn):
    conn.sendall(b"NOTFOUND\n")

def handle(conn, addr):
    try:
        line = recv_line(conn)
        if not line.startswith("GET "):
            send_notfound(conn); return
        rel = line[4:].strip().lstrip("/")
        path = os.path.normpath(os.path.join(ROOT, rel))
        if not path.startswith(ROOT):
            send_notfound(conn); return
        if os.path.isfile(path):
            with open(path, "rb") as f: data = f.read()
            send_found(conn, data)
            print(f"[SERVER2] Sent {rel} ({len(data)} bytes) to {addr}")
        else:
            send_notfound(conn)
            print(f"[SERVER2] {rel} not found for {addr}")
    except Exception as e:
        print("[SERVER2] Error:", e)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[SERVER2] Listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn: handle(conn, addr)

if __name__ == "__main__":
    main()

