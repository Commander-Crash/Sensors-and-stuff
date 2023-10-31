from sense_hat import SenseHat
import socket
import subprocess

def start_receiver(ip, port):
    sense = SenseHat()
    # Set rotation
    sense.set_rotation(90)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip, port))
    server_socket.listen(1)

    print(f"Listening for connections on {ip}:{port}")

    while True:
        connection, client_address = server_socket.accept()
        message = connection.recv(1024).decode()

        # Display on Sense HAT
        sense.show_message(message, text_colour=(255, 0, 0), back_colour=(0, 0, 0), scroll_speed=0.05)

        connection.close()

if __name__ == "__main__":
    target_ip = "0.0.0.0"  # Listen on all available interfaces
    target_port = 2233

    try:
        start_receiver(target_ip, target_port)
    except KeyboardInterrupt:
        pass
