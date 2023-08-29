import socket
import threading

clients = []
unsent_messages = []

def receive(sock):
    while True:
        try:
            data, addr = sock.recvfrom(2000)
            msg = data.decode('utf-8')
            msg = msg.replace("_command", "command")
            print("msgs",addr, msg)
            if addr not in clients:
                clients.append(addr)
            unsent_messages.append(data)
        except:
            pass


def broadcast(sock):
    while True:
        if len(unsent_messages) > 0:
            data = unsent_messages.pop(0)
            for client in clients:
                try:
                    sock.sendto(data, client)
                except:
                    clients.remove(client)
                    unsent_messages.append(f"[SERVER] Goodbye {client}!".encode('utf-8'))

def main(SERVER_PORT):
    SERVER_IP = socket.gethostbyname(socket.gethostname())

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind((SERVER_IP, SERVER_PORT))
    #print(f"Listening on {SERVER_IP}:{SERVER_PORT}")

    threading.Thread(target=receive, args=(sock, )).start()
    threading.Thread(target=broadcast, args=(sock, )).start()