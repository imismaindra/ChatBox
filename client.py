import socket
import datetime
import os
import threading

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

def main():
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


if __name__ == "__main__":
    main()