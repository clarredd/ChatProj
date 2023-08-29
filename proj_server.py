import socket
import threading

clients = []
unsent_messages = dict()
command_next = False
chat_users = {"pub":[], "server":[]}
chat_user_perms = {"pub":[],"server":[]}
chat_configs = {"pub":{"erasable":False,"joinable":True},"server":{"erasable":False,"joinable":False}}
user_chats = dict()
user_curr = dict()
admin_num = {"pub":0,"server":0}
any_received = dict()
addr_of = dict()

last_chat = dict()
def chats_message(client, chat, mess):
    global last_chat
    cont = client in last_chat.keys()
    if not cont or cont and last_chat[client] != chat:
        unsent_messages[client].append("chat")
        unsent_messages[client].append(chat)
        last_chat[client] = chat
    unsent_messages[client].append(mess)

def receive(sock):
    while True:
        try:
            data, addr = sock.recvfrom(2000)
            msg = data.decode('utf-8')
            msg = msg.replace("_command", "command")
            if msg == "command":
                command_next = True
                print("msgs",addr, msg)
                continue
            if command_next:
                command_next = False
                username, message = msg.split("]:",1)
                username = username[1:]
                params = message.split()
                command_name = params[0]
                
                if command_name == "create_chat":
                    chat_name = params[1]
                    if chat_name in chat_users.keys():
                        chats_message(addr, "server", "Chat not created. The name is already taken. ")
                    elif " " in chat_name:
                        chats_message(addr, "server", "Chat not created. The name is invalid. ")
                    else:
                        chats_message(addr, "server", "Chat "+chat_name+" created. ")
                        chat_users[chat_name] = [addr]
                        user_chats[addr].append(chat_name)
                        chat_user_perms[chat_name] = {addr:{"writer":True,"configurer":False,"moderator":False,"admin":True,"banned":False,"reader":True}}
                        chat_configs[chat_name] = {"erasable":True,"joinable":True}
                elif command_name == "leave_chat":
                    if len(params)<2:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = params[1]
                    if chat_name == "server" or chat_name == "pub":
                        chats_message(addr, "server", "Chat not left. You cannot leave the base chats. ")
                    elif not(chat_name in user_chats[addr]):
                        chats_message(addr, "server", "Chat not left. You are no member of the chat. ")
                    elif chat_user_perms[chat_name][addr]["banned"]:
                        chats_message(addr, "server", "Chat not left. You are banned. ")
                    elif chat_user_perms[chat_name][addr]["admin"] and admin_num[chat_name]==1:
                        chats_message(addr, "server", "Chat not left. You are the only admin. ")
                    else:
                        chats_message(addr, "server", "Chat "+chat_name+" left. ")
                        chat_users[chat_name].remove(addr)
                        user_chats[addr].remove(chat_name)
                        del chat_user_perms[chat_name][addr]
                elif command_name == "ban":
                    if len(params)<2:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = user_curr[addr]
                    user_name = params[1]
                    if not(user_addr in addr_of.keys()):
                        chats_message(addr, "server", "User not banned. Invalid username. ")
                        continue
                    user_addr = addr_of[user_name]
                    if not(user_addr in chat_users[chat_name]):
                        chats_message(addr, "server", "User not banned. User is no member of the chat. ")
                    elif chat_user_perms[chat_name][addr]["admin"]:
                        chats_message(addr, "server", "User '"+user_name+"' banned. ")
                        chat_user_perms[chat_name][user_addr] = {"writer":False,"configurer":False,"moderator":False,"admin":False,"banned":True,"reader":False}
                    else:
                        chats_message(addr, "server", "User not banned. You are no admin. ")
                elif command_name == "enter_chat":
                    if len(params)<2:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = params[1]
                    if not(chat_name in chat_users.keys()):
                        chats_message(addr, "server", "Chat not entered. Invalid chat name. ")
                    elif addr in chat_users[chat_name]:
                        chats_message(addr, "server", "Chat not entered. You are already a member of the chat. ")
                    elif not chat_configs[chat_name]["joinable"]:
                        chats_message(addr, "server", "Chat not entered. The chat isn't joinable. ")
                    else:
                        chats_message(addr, "server", "Chat "+chat_name+" entered. ")
                        user_chats[addr].append(chat_name)
                        chat_users[chat_name].append(addr)
                        chat_user_perms[chat_name][addr]
                elif command_name == "list_chats":
                    message = ""
                    for ch in user_chats[addr]:
                        if ch == user_curr[addr]:
                            message += "* "
                        message += ch + "\n"
                    chats_message(addr, "server", message)
                elif command_name == "chat_config":
                    if len(params)<2:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = params[1]
                    if not(chat_name in chat_users.keys()):
                        chats_message(addr, "server", "Chat not entered. Invalid chat name. ")
                    if len(params)<3:
                        message = "The chat:\n"
                        for k, v in chat_configs[chat_name]:
                            message += "is "
                            if not v:
                                message += "not "
                            message += k
                            chats_message(addr, "server", "Chat not entered. Invalid chat name. ")
                        continue
                elif command_name == "user_perms":
                    if len(params)<3:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = params[1]
                    if not(chat_name in chat_users.keys()):
                        chats_message(addr, "server", "User permissions not available. Invalid chat name. ")
                    user_name = params[2]
                    user_addr = addr_of[user_name]
                    if not(chat_name in chat_users.keys()):
                        chats_message(addr, "server", "Chat not entered. Invalid chat name. ")
                    if len(params)<4:
                        message = "The user:\n"
                        for k, v in chat_user_perms[chat_name][]:
                            message += "is "
                            if not v:
                                message += "not "
                            message += k
                        continue
                else:
                    chats_message(addr, "server", "Invalid command. ")

            print("msgs",addr, msg)
            if addr not in clients:
                clients.append(addr)
                user_curr[addr] = "pub"
                chat_users["pub"].append(addr)
                chat_users["server"].append(addr)
                chat_user_perms["pub"][addr] = {"writer":True,"configurer":False,"moderator":False,"admin":False,"banned":False,"reader":True}
                chat_user_perms["server"][addr] = {"writer":False,"configurer":False,"moderator":False,"admin":False,"banned":False,"reader":True}
            unsent_messages.append(data)
        except:
            pass


def broadcast(sock):
    while True:
        for client in clients:
            if len(unsent_messages[client]) > 0:
                data = unsent_messages[client].pop(0)
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