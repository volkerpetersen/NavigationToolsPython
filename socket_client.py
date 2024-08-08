import socket


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 2053  # socket server port number
    print(f"Client is connecting to {host} {port}")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # instantiate
    client_socket.settimeout(20)
    client_socket.connect((host, port))  # connect to the server

    message = input(" -> ")  # take input

    while message.lower().strip() != 'bye':
        client_socket.send(message.encode())      # send message
        data = client_socket.recv(1024).decode()  # receive response

        print('CLIENT: Received from server: ' + data)  # show in terminal

        message = input(" -> ")  # again take input

    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()