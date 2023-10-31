import socket

def send_message(message, ip, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((ip, port))
    client_socket.send(message.encode())
    client_socket.close()

if __name__ == "__main__":
    target_ip = "192.168.3.100"
    target_port = 2233

    message = "5GHZ COX DETECTED"
    send_message(message, target_ip, target_port)
