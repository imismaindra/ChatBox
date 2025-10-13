import socket
import threading

def handle_client(conn, addr):
    """Fungsi untuk menangani setiap client"""
    print(f"[NEW CONNECTION] {addr} connected")
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            print(f"[{addr}] Received: {data}")
            conn.send(f"Server received: {data}".encode())
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 8080))
    server.listen(5)
    print("[STARTING] Server is listening on port 8080...")
    
    try:
        while True:
            conn, addr = server.accept()
            # Buat thread baru untuk setiap client
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("\n[SHUTTING DOWN] Server stopped")
        server.close()

if __name__ == "__main__":
    start_server()