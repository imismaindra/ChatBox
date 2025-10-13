import socket

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
    
        # Input pesan dari user
        message = input("Masukkan pesan yang ingin dikirim: ")
    
        # Mengirim pesan ke server
        client.send(message.encode())
        print(f"Pesan terkirim: {message}")
    
        # Menerima response dari server
        response = client.recv(1024).decode()
        print(f"Received response: {response}")
    
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