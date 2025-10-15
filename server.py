import socket
import threading
import datetime
import os

HOST = '172.18.3.195' 
PORT = 8081

# Buat direktori untuk menyimpan log jika belum ada
LOG_DIR = "chat_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# List untuk menyimpan semua client yang terhubung
connected_clients = []

def log_message(client_addr, message, message_type="RECEIVED"):
    """Fungsi untuk menyimpan log percakapan"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(LOG_DIR, f"chat_history_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt")
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {client_addr} - {message_type}: {message}\n")

def broadcast_message(message, sender_addr, sender_conn):
    """Fungsi untuk mengirim pesan ke semua client kecuali pengirim"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {sender_addr[0]}: {message}"
    
    # Kirim ke semua client kecuali pengirim
    for client_conn, client_addr in connected_clients:
        if client_conn != sender_conn:
            try:
                client_conn.send(formatted_message.encode())
            except:
                # Jika gagal kirim, hapus client dari list
                connected_clients.remove((client_conn, client_addr))
                client_conn.close()
    
    # Log broadcast
    log_message(sender_addr, f"BROADCAST: {message}", "BROADCAST")

def handle_client(conn, addr):
    """Fungsi untuk menangani setiap client"""
    print(f"[NEW CONNECTION] {addr} connected")
    log_message(addr, "CLIENT CONNECTED", "SYSTEM")
    
    # Tambahkan client ke list
    connected_clients.append((conn, addr))
    print(f"[ACTIVE CONNECTIONS] {len(connected_clients)}")
    
    # Kirim notifikasi ke semua client bahwa ada client baru
    broadcast_message(f"User {addr[0]} joined the chat", addr, conn)
    
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            
            print(f"[{addr}] Received: {data}")
            # Log pesan yang diterima
            log_message(addr, data, "RECEIVED")
            
            # Broadcast pesan ke semua client lain
            broadcast_message(data, addr, conn)
            
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
        log_message(addr, f"ERROR: {e}", "SYSTEM")
    finally:
        # Hapus client dari list
        if (conn, addr) in connected_clients:
            connected_clients.remove((conn, addr))
        
        # Notifikasi ke semua client bahwa ada client yang keluar
        broadcast_message(f"User {addr[0]} left the chat", addr, conn)
        
        conn.close()
        print(f"[DISCONNECTED] {addr}")
        print(f"[ACTIVE CONNECTIONS] {len(connected_clients)}")
        log_message(addr, "CLIENT DISCONNECTED", "SYSTEM")

def server_chat_input():
    """Fungsi untuk server mengirim pesan ke semua client"""
    print("\nServer dapat mengirim pesan ke semua client!")
    print("Ketik pesan server atau 'quit' untuk keluar dari mode chat server")
    print("-" * 50)
    
    while True:
        try:
            server_message = input("Server: ")
            if server_message.lower() == 'quit':
                print("Server keluar dari mode chat")
                break
            
            if connected_clients:
                # Broadcast pesan server ke semua client
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] SERVER: {server_message}"
                
                for client_conn, client_addr in connected_clients:
                    try:
                        client_conn.send(formatted_message.encode())
                    except:
                        # Jika gagal kirim, hapus client dari list
                        connected_clients.remove((client_conn, client_addr))
                        client_conn.close()
                
                # Log pesan server
                log_message(("SERVER", 0), f"SERVER MESSAGE: {server_message}", "SERVER")
                print(f"Pesan server terkirim ke {len(connected_clients)} client")
            else:
                print("Tidak ada client yang terhubung")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error server chat: {e}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[STARTING] Server berjalan di {HOST}:{PORT} ...")
    print("Server dapat mengirim pesan ke semua client!")
    
    # Buat thread untuk server chat input
    server_chat_thread = threading.Thread(target=server_chat_input)
    server_chat_thread.daemon = True
    server_chat_thread.start()
    
    try:
        while True:
            conn, addr = server.accept()
            # Buat thread baru untuk setiap client
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[SHUTTING DOWN] Server stopped")
        server.close()

if __name__ == "__main__":
    start_server()