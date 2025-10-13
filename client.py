import socket

# Membuat socket client
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Koneksi ke server
    client.connect(('localhost', 8080))
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