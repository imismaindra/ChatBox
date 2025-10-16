import socket
import datetime
import os
import threading
import sys
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    from tkinter.scrolledtext import ScrolledText
except Exception:
    tk = None

# Buat direktori untuk menyimpan log jika belum ada
LOG_DIR = "chat_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def log_message(message, message_type="SENT", server_response=""):
    """Fungsi untuk menyimpan log percakapan di client"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(LOG_DIR, f"client_chat_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt")
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] CLIENT - {message_type}: {message}\n")
        if server_response:
            f.write(f"[{timestamp}] SERVER RESPONSE: {server_response}\n")

def show_chat_history():
    """Fungsi untuk menampilkan riwayat chat hari ini"""
    log_file = os.path.join(LOG_DIR, f"client_chat_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt")
    
    if os.path.exists(log_file):
        print("\n" + "="*50)
        print("RIWAYAT CHAT HARI INI")
        print("="*50)
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Tampilkan 10 pesan terakhir
                for line in lines[-10:]:
                    print(line.strip())
        except Exception as e:
            print(f"Error membaca file log: {e}")
        print("="*50 + "\n")
    else:
        print("Belum ada riwayat chat hari ini.")

def receive_messages(client):
    """Fungsi untuk menerima pesan dari server/client lain"""
    try:
        while True:
            message = client.recv(1024).decode()
            if not message:
                break
            
            # Tampilkan pesan yang diterima
            print(f"\n{message}")
            print("Anda: ", end="", flush=True)
            
            # Log pesan yang diterima
            log_message(message, "RECEIVED")
            
    except Exception as e:
        print(f"\nError receiving message: {e}")

def cli_main():
    # Input IP dan port server (LAN IP dari laptop server)
    server_ip = input("Masukkan IP server (contoh 192.168.1.10): ").strip() or '127.0.0.1'
    port_str = input("Masukkan port (default 8081): ").strip() or '8081'
    try:
        server_port = int(port_str)
    except ValueError:
        print("Port tidak valid. Gunakan angka, contoh 8081.")
        return

    # Membuat socket client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Koneksi ke server
        client.connect((server_ip, server_port))
        print("Berhasil terhubung ke server!")
        print("Ketik 'quit' untuk keluar dari chat")
        print("Ketik 'history' untuk melihat riwayat chat hari ini")
        print("-" * 40)
        
        # Log koneksi berhasil
        log_message("CONNECTED TO SERVER", "SYSTEM")
        
        # Buat thread untuk menerima pesan
        receive_thread = threading.Thread(target=receive_messages, args=(client,))
        receive_thread.daemon = True
        receive_thread.start()
        
        while True:
            # Input pesan dari user
            message = input("Anda: ")
            
            # Cek apakah user ingin keluar
            if message.lower() == 'quit':
                print("Keluar dari chat...")
                log_message("DISCONNECTED FROM SERVER", "SYSTEM")
                break
            
            # Cek apakah user ingin melihat history
            if message.lower() == 'history':
                show_chat_history()
                continue
            
            # Mengirim pesan ke server
            client.send(message.encode())
            print(f"Pesan terkirim: {message}")
            
            # Log pesan yang dikirim
            log_message(message, "SENT")
        
    except ConnectionRefusedError:
        print("Gagal terhubung ke server. Pastikan server sudah berjalan.")
    except Exception as e:
        print(f"Terjadi error: {e}")
    finally:
        # Menutup koneksi
        client.close()
        print("Koneksi ditutup.")

class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        self.client = None
        self.receiver_thread = None
        self.connected = False

        container = ttk.Frame(root, padding=10)
        container.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        conn_frame = ttk.Frame(container)
        conn_frame.grid(row=0, column=0, sticky="ew")
        conn_frame.columnconfigure(5, weight=1)

        ttk.Label(conn_frame, text="IP:").grid(row=0, column=0, padx=(0,5))
        self.ip_var = tk.StringVar(value="127.0.0.1")
        self.ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=16)
        self.ip_entry.grid(row=0, column=1)

        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=(10,5))
        self.port_var = tk.StringVar(value="8081")
        self.port_entry = ttk.Entry(conn_frame, textvariable=self.port_var, width=8)
        self.port_entry.grid(row=0, column=3)

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connect)
        self.connect_btn.grid(row=0, column=4, padx=(10,0))

        self.history_btn = ttk.Button(conn_frame, text="History", command=self.show_history_popup)
        self.history_btn.grid(row=0, column=5, sticky="e")

        self.chat_box = ScrolledText(container, height=18, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_box.grid(row=1, column=0, sticky="nsew", pady=(10,10))
        container.rowconfigure(1, weight=1)

        input_frame = ttk.Frame(container)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)

        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(input_frame, textvariable=self.message_var)
        self.message_entry.grid(row=0, column=0, sticky="ew")
        self.message_entry.bind("<Return>", lambda _e: self.send_message())

        self.send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        self.send_btn.grid(row=0, column=1, padx=(8,0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def append_text(self, text):
        self.chat_box.configure(state=tk.NORMAL)
        self.chat_box.insert(tk.END, text + "\n")
        self.chat_box.see(tk.END)
        self.chat_box.configure(state=tk.DISABLED)

    def toggle_connect(self):
        if not self.connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        ip = self.ip_var.get().strip() or "127.0.0.1"
        try:
            port = int(self.port_var.get().strip() or "8081")
        except ValueError:
            messagebox.showerror("Error", "Port tidak valid. Gunakan angka, contoh 8081.")
            return

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((ip, port))
        except Exception as e:
            messagebox.showerror("Koneksi Gagal", f"Gagal terhubung: {e}")
            self.client.close()
            self.client = None
            return

        self.connected = True
        self.connect_btn.configure(text="Disconnect")
        self.append_text("Berhasil terhubung ke server!")
        log_message("CONNECTED TO SERVER", "SYSTEM")

        self.receiver_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receiver_thread.start()

    def disconnect(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.client = None
        if self.connected:
            log_message("DISCONNECTED FROM SERVER", "SYSTEM")
        self.connected = False
        self.connect_btn.configure(text="Connect")
        self.append_text("Koneksi ditutup.")

    def receive_loop(self):
        try:
            while self.connected and self.client:
                try:
                    data = self.client.recv(1024)
                    if not data:
                        break
                    message = data.decode()
                    log_message(message, "RECEIVED")
                    self.root.after(0, lambda m=message: self.append_text(m))
                except OSError:
                    break
                except Exception as e:
                    self.root.after(0, lambda: self.append_text(f"Error receiving message: {e}"))
                    break
        finally:
            self.root.after(0, self.disconnect)

    def send_message(self):
        if not self.connected or not self.client:
            messagebox.showwarning("Tidak Terhubung", "Silakan connect ke server terlebih dahulu.")
            return
        message = self.message_var.get().strip()
        if not message:
            return
        try:
            self.client.send(message.encode())
            self.append_text(f"Pesan terkirim: {message}")
            log_message(message, "SENT")
            self.message_var.set("")
        except Exception as e:
            messagebox.showerror("Gagal Mengirim", str(e))

    def show_history_popup(self):
        log_file = os.path.join(LOG_DIR, f"client_chat_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt")
        if not os.path.exists(log_file):
            messagebox.showinfo("Riwayat", "Belum ada riwayat chat hari ini.")
            return
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            last_lines = "".join(lines[-10:]) or "(Kosong)"
            history_win = tk.Toplevel(self.root)
            history_win.title("Riwayat Chat Hari Ini")
            text = ScrolledText(history_win, width=80, height=20, state=tk.NORMAL)
            text.pack(fill=tk.BOTH, expand=True)
            text.insert(tk.END, last_lines)
            text.configure(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Error membaca file log: {e}")

    def on_close(self):
        self.disconnect()
        self.root.destroy()

def gui_main():
    if tk is None:
        print("Tkinter tidak tersedia. Menjalankan mode CLI.")
        cli_main()
        return
    root = tk.Tk()
    ChatClientGUI(root)
    root.minsize(600, 420)
    root.mainloop()


if __name__ == "__main__":
    # Jalankan GUI secara default; gunakan argumen 'cli' untuk mode terminal
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'cli':
        cli_main()
    else:
        gui_main()