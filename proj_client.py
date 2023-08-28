import socket
import threading
import random

log_r = ""
mbuff_s = None
en = False
r_pid = None # *ne PID
inter_load = False

def create_client_chat_socket(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    client_port = None
    while not client_port:
        port = random.randint(10000, 20000)
        try:
            sock.bind(("0.0.0.0", port))
            client_port = port
        except:
            pass
    
    return sock

def receive(sock, lock, interl_id):
    global r_pid, en, log_r, inter_load
    local = threading.local()
    while lock.locked():
        pass
    lock.acquire()
    local.log = log_r
    lock.release()
    while True:
        local.data, local.addr = sock.recvfrom(2000)
        local.msg = local.data.decode('utf-8')
        local.log += local.msg + "\n"
        while lock.locked():
            pass
        lock.acquire()
        log_r = local.log
        r_pid = interl_id
        inter_load = False
        en = True
        while en:
            pass
        lock.release() # Ovde je da se ne bi desilo vise pristupa flag-ovima. 

def interl():
    global en, r_id, inter_load
    local = threading.local()
    local.log = ""
    while True:
        if en and r_pid == threading.get_ident():
            if inter_load:
                local.log = log_r
                inter_load = False
            else:
                log_r = local.log
            en = False

def send(ip, port, name, sock):
    global en, r_pid, mbuff_s
    local = threading.local()
    sock.sendto(f"{name} has joined the chat!".encode('utf-8'), (ip, port))
    while True:
        local.msg = None
        while not en or r_pid != threading.get_ident():
            pass
        local.msg = mbuff_s
        en = False
        sock.sendto(f"[{name}]: {local.msg}".encode('utf-8'), (ip, port))

def main(server_ip, server_port, name):
    sock = create_client_chat_socket(server_ip)

    global lock
    lock = threading.Lock()
    rec_th = threading.Thread(target=interl, args=tuple())
    rec_th.start()
    threading.Thread(target=receive, args=(sock, lock, rec_th.ident)).start()
    sen_th = threading.Thread(target=send, args=(server_ip, server_port, name, sock))
    sen_th.start()
    return sen_th.ident,rec_th.ident

def getlog(r):
    global en, r_pid
    while lock.locked():
        pass
    lock.acquire()
    r_pid = r
    en = True
    lock.release()
    while en:
        pass
    return log_r

def msgbuffput(v, r):
    global mbuff_s, en, r_pid
    while lock.locked():
        pass
    lock.acquire()
    mbuff_s = v
    r_pid = r
    en = True
    lock.release()
    while en:
        pass