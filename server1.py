#!/usr/bin/env python3
import socket, os

HOST = "0.0.0.0"
PORT = 5001
SERVER2_IP = "172.31.xx.yy"   # <-- replace with SERVER2 private IP
SERVER2_PORT = 5002
ROOT = os.path.expanduser("~/file_storage")

def recv_line(conn):
    buf = bytearray()
    while True:
        b = conn.recv(1)
        if not b: break
        buf += b
        if buf.endswith(b"\n"): break
    return bytes(buf).decode(errors="replace").rstrip("\n")

def recv_exact(conn, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk: raise ConnectionError("socket closed early")
        buf += chunk
    return bytes(buf)

def get_from_server2(filename: str) -> bytes | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
            s2.connect((SERVER2_IP, SERVER2_PORT))
            s2.sendall(f"GET {filename}\n".encode())
            header = recv_line(s2)
            if header == "NOTFOUND": return None
            if header.startswith("FOUND "):
                length = int(header.split()[1])
                return recv_exact(s2, length)
    except Exception as e:
        print("[SERVER1] Error contacting SERVER2:", e)
    return None

def read_local(filename: str) -> bytes | None:
    rel = filename.lstrip("/")
    path = os.path.normpath(os.path.join(ROOT, rel))
    if not path.startswith(ROOT): return None
    if os.path.isfile(path):
        with open(path, "rb") as f: return f.read()
    return None

def send_one(conn, data: bytes):
    conn.sendall(f"OK ONE {len(data)}\n".encode() + data)

def send_both(conn, d1: bytes, d2: bytes):
    conn.sendall(f"OK BOTH {len(d1)} {len(d2)}\n".encode() + d1 + d2)

def send_error(conn, msg="ERROR NOTFOUND"):
    conn.sendall((msg + "\n").encode())

def handle_client(conn, addr):
    try:
        line = recv_line(conn)
        if not line.startswith("GET "):
            send_error(conn, "ERROR BADREQUEST"); return
        filename = line[4:].strip()
        print(f"[SERVER1] CLIENT {addr} requested {filename}")

        local = read_local(filename)
        remote = get_from_server2(filename)

        if local and remote:
            if local == remote:
                send_one(conn, local)
                print("[SERVER1] Both matched → sent ONE")
            else:
                send_both(conn, local, remote)
                print("[SERVER1] Versions differ → sent BOTH")
        elif local:
            send_one(conn, local)
            print("[SERVER1] Only SERVER1 had it → sent ONE")
        elif remote:
            send_one(conn, remote)
            print("[SERVER1] Only SERVER2 had it → sent ONE")
        else:
            send_error(conn)
            print("[SERVER1] Not found on either")
    except Exception as e:
        print("[SERVER1] Error:", e)
        try: send_error(conn, "ERROR INTERNAL")
        except: pass

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s1.bind((HOST, PORT))
        s1.listen()
        print(f"[SERVER1] Listening on {HOST}:{PORT}")
        while True:
            conn, addr = s1.accept()
            with conn: handle_client(conn, addr)

if __name__ == "__main__":
    main()

