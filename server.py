import socket
import threading
import datetime
import os
import signal
import sys
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    from tkinter.scrolledtext import ScrolledText
except Exception:
    tk = None

# Gunakan HOST/PORT dari environment bila ada; default ke semua interface
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '8081'))

# Buat direktori untuk menyimpan log 
LOG_DIR = "chat_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# List untuk menyimpan semua client yang terhubung
connected_clients = []
# List untuk menyimpan semua thread client
client_threads = []
# Flag untuk mengontrol server
server_running = True

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
        while server_running:
            try:
                # Set timeout untuk recv agar bisa check server_running flag
                conn.settimeout(1.0)
                data = conn.recv(1024).decode()
                if not data:
                    break
                
                print(f"[{addr}] Received: {data}")
                # Log pesan yang diterima
                log_message(addr, data, "RECEIVED")
                
                # Broadcast pesan ke semua client lain
                broadcast_message(data, addr, conn)
            except socket.timeout:
                # Timeout, check server_running flag
                continue
            except Exception as e:
                print(f"[ERROR] {addr}: {e}")
                log_message(addr, f"ERROR: {e}", "SYSTEM")
                break
            
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
        log_message(addr, f"ERROR: {e}", "SYSTEM")
    finally:
        # Hapus client dari list
        if (conn, addr) in connected_clients:
            connected_clients.remove((conn, addr))
        
        # Notifikasi ke semua client bahwa ada client yang keluar
        if server_running:
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
    
    while server_running:
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
            print("\nServer chat interrupted")
            break
        except Exception as e:
            print(f"Error server chat: {e}")

def broadcast_from_server(message: str):
    """Broadcast helper dipanggil dari GUI"""
    if not message:
        return 0
    delivered = 0
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] SERVER: {message}"
    for client_conn, client_addr in connected_clients[:]:
        try:
            client_conn.send(formatted_message.encode())
            delivered += 1
        except Exception:
            try:
                connected_clients.remove((client_conn, client_addr))
            except Exception:
                pass
            try:
                client_conn.close()
            except Exception:
                pass
    log_message(("SERVER", 0), f"SERVER MESSAGE: {message}", "SERVER")
    return delivered

def shutdown_server():
    """Fungsi untuk shutdown server dengan proper cleanup"""
    global server_running
    print("\n[SHUTTING DOWN] Server sedang dimatikan...")
    server_running = False
    
    # Tutup semua koneksi client
    for client_conn, client_addr in connected_clients[:]:
        try:
            client_conn.close()
        except:
            pass
    connected_clients.clear()
    
    # Tunggu semua thread client selesai
    for thread in client_threads[:]:
        if thread.is_alive():
            thread.join(timeout=2.0)
    client_threads.clear()
    
    print("[SHUTDOWN COMPLETE] Server berhasil dimatikan")

def signal_handler(signum, frame):
    """Handler untuk signal SIGINT dan SIGTERM"""
    print(f"\n[RECEIVED SIGNAL {signum}] Server akan dimatikan...")
    shutdown_server()
    sys.exit(0)

def start_server():
    global server_running
    server_running = True
    
    # Register signal handler hanya jika di main thread
    try:
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, signal_handler)
            # SIGTERM mungkin tidak tersedia di Windows, tangani dengan aman
            try:
                signal.signal(signal.SIGTERM, signal_handler)
            except Exception:
                pass
    except Exception:
        # Abaikan jika tidak bisa set signal (mis. bukan main thread)
        pass
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[STARTING] Server berjalan di {HOST}:{PORT} ...")
    print("Server dapat mengirim pesan ke semua client!")
    print("Tekan Ctrl+C untuk menghentikan server")
    
    # Buat thread untuk server chat input
    server_chat_thread = threading.Thread(target=server_chat_input)
    server_chat_thread.daemon = True
    server_chat_thread.start()
    
    try:
        while server_running:
            try:
                # Set timeout untuk accept agar bisa check server_running flag
                server.settimeout(1.0)
                conn, addr = server.accept()
                
                # Buat thread baru untuk setiap client
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
                client_threads.append(thread)
                
            except socket.timeout:
                # Timeout, check server_running flag
                continue
            except Exception as e:
                if server_running:
                    print(f"[ERROR] Accept connection: {e}")
                    
    except KeyboardInterrupt:
        print("\n[KEYBOARD INTERRUPT] Server dimatikan oleh user")
    finally:
        shutdown_server()
        server.close()

def cli_main():
    start_server()

class ServerControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Server Control")
        self.server_thread = None
        self.running = False

        container = ttk.Frame(root, padding=10)
        container.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        cfg = ttk.Frame(container)
        cfg.grid(row=0, column=0, sticky="ew")
        cfg.columnconfigure(4, weight=1)

        ttk.Label(cfg, text="Host:").grid(row=0, column=0, padx=(0,5))
        self.host_var = tk.StringVar(value=str(HOST))
        self.host_entry = ttk.Entry(cfg, textvariable=self.host_var, width=16)
        self.host_entry.grid(row=0, column=1)

        ttk.Label(cfg, text="Port:").grid(row=0, column=2, padx=(10,5))
        self.port_var = tk.StringVar(value=str(PORT))
        self.port_entry = ttk.Entry(cfg, textvariable=self.port_var, width=8)
        self.port_entry.grid(row=0, column=3)

        self.toggle_btn = ttk.Button(cfg, text="Start Server", command=self.toggle_server)
        self.toggle_btn.grid(row=0, column=4, sticky="e")

        self.log_box = ScrolledText(container, height=18, wrap=tk.WORD, state=tk.DISABLED)
        self.log_box.grid(row=1, column=0, sticky="nsew", pady=(10,10))
        container.rowconfigure(1, weight=1)

        bcast = ttk.Frame(container)
        bcast.grid(row=2, column=0, sticky="ew")
        bcast.columnconfigure(0, weight=1)

        self.msg_var = tk.StringVar()
        self.msg_entry = ttk.Entry(bcast, textvariable=self.msg_var)
        self.msg_entry.grid(row=0, column=0, sticky="ew")
        self.msg_entry.bind("<Return>", lambda _e: self.send_broadcast())
        self.send_btn = ttk.Button(bcast, text="Broadcast", command=self.send_broadcast)
        self.send_btn.grid(row=0, column=1, padx=(8,0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def append_log(self, text):
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def toggle_server(self):
        if not self.running:
            self.start_server_gui()
        else:
            self.stop_server_gui()

    def start_server_gui(self):
        host = self.host_var.get().strip() or "0.0.0.0"
        try:
            port = int(self.port_var.get().strip() or "8081")
        except ValueError:
            messagebox.showerror("Error", "Port tidak valid.")
            return

        os.environ['HOST'] = host
        os.environ['PORT'] = str(port)

        self.running = True
        self.toggle_btn.configure(text="Stop Server")
        self.append_log(f"Starting server on {host}:{port} ...")

        # Jalankan server di thread terpisah
        self.server_thread = threading.Thread(target=start_server, daemon=True)
        self.server_thread.start()

    def stop_server_gui(self):
        if self.running:
            self.append_log("Stopping server ...")
            shutdown_server()
            self.running = False
            self.toggle_btn.configure(text="Start Server")

    def send_broadcast(self):
        msg = self.msg_var.get().strip()
        if not msg:
            return
        delivered = broadcast_from_server(msg)
        self.append_log(f"Broadcast terkirim ke {delivered} client")
        self.msg_var.set("")

    def on_close(self):
        self.stop_server_gui()
        self.root.destroy()

def gui_main():
    if tk is None:
        print("Tkinter tidak tersedia. Menjalankan mode CLI.")
        cli_main()
        return
    root = tk.Tk()
    ServerControlGUI(root)
    root.minsize(640, 460)
    root.mainloop()

if __name__ == "__main__":
    # Default ke GUI; gunakan argumen 'cli' untuk mode terminal
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'cli':
        cli_main()
    else:
        gui_main()