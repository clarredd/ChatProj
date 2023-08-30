import socket
import threading
from traceback import print_exc

clients = []
unsent_messages = dict()
command_next = False
chat_users = {"pub":[], "server":[]}
chat_user_perms = {"pub":{},"server":{}}
chat_configs = {"pub":{"erasable":False,"joinable":True},"server":{"erasable":False,"joinable":False}}
user_chats = dict()
user_curr = dict()
admin_num = {"pub":0,"server":0}
addr_of = dict()
username_of = dict()

last_chat = dict()
last_view = dict()
def chats_message(client, chat, mess):
    global unsent_messages, last_chat, last_view, user_curr
    while lock.locked():
        pass
    lock.acquire()
    cont = client in last_chat.keys()
    if not cont or cont and last_chat[client] != chat:
        unsent_messages[client].append({"data":"chat".encode("utf-8"),"targets":[client]})
        unsent_messages[client].append({"data":chat.encode("utf-8"),"targets":[client]})
        last_chat[client] = chat
    viet = client in last_view.keys()
    if not viet or viet and last_view[client] != user_curr[client]:
        unsent_messages[client].append({"data":"view".encode("utf-8"),"targets":[client]})
        unsent_messages[client].append({"data":user_curr[client].encode("utf-8"),"targets":[client]})
        last_view[client] = user_curr[client]
    readers = []
    for u in chat_users[user_curr[client]]:
        if chat_user_perms[user_curr[client]][u]["reader"]:
            readers.append(u)
    unsent_messages[client].append({"data":mess.encode("utf-8"),"targets":readers})
    print("Sending",mess,"@",chat)
    lock.release()

def receive(sock):
    global clients, unsent_messages, command_next, chat_users, chat_user_perms, chat_configs, user_chats, user_curr, admin_num, addr_of, lock, username_of
    while True:
        try:
            data, addr = sock.recvfrom(2000)
            msg = data.decode('utf-8')
            addr = str(addr)
            print("msgs",addr, msg)
            msg = msg.replace("_command", "command")
            if msg == "command":
                command_next = True
                continue
            if command_next:
                command_next = False
                message = msg
                params = message.split()
                command_name = params[0]
                
                if command_name == "create_chat":
                    if len(params)<2:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = params[1]
                    if chat_name in chat_users.keys():
                        chats_message(addr, "server", "Chat not created. The name is already taken. ")
                    elif " " in chat_name:
                        chats_message(addr, "server", "Chat not created. The name is invalid. ")
                    else:
                        chat_users[chat_name] = [addr]
                        user_chats[addr].append(chat_name)
                        chat_user_perms[chat_name] = {addr:{"writer":True,"configurer":False,"moderator":False,"admin":True,"banned":False,"reader":True}}
                        chat_configs[chat_name] = {"erasable":True,"joinable":True}
                        admin_num[chat_name] = 1
                        chats_message(addr, chat_name, "[SERVER] Welcome too your new fresh chat. ")
                        chats_message(addr, "server", "Chat "+chat_name+" created. ")
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
                    elif chat_user_perms[chat_name][addr]["admin"] and admin_num[chat_name]==1 and chat_configs[chat_name]["erasable"]:
                        chats_message(addr, "server", "Chat not left. You are the only admin. ")
                    else:
                        if chat_user_perms[chat_name][addr]["admin"]:
                            admin_num[chat_name]-=1
                        chat_users[chat_name].remove(addr)
                        user_chats[addr].remove(chat_name)
                        del chat_user_perms[chat_name][addr]
                        if admin_num[chat_name] == 0:
                            del chat_configs[chat_name]
                            del chat_user_perms[chat_name]
                            del admin_num[chat_name]
                            for u in chat_users[chat_name]:
                                user_chats[u].remove(chat_name)
                            del chat_users[chat_name]
                        chats_message(addr, "server", "Chat "+chat_name+" left. ")
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
                        user_curr[addr] = chat_name
                        chats_message(addr, "server", "Chat selected as the current. You are already a member of the chat. ")
                    elif not chat_configs[chat_name]["joinable"]:
                        chats_message(addr, "server", "Chat not entered. The chat isn't joinable. ")
                    else:
                        user_chats[addr].append(chat_name)
                        chat_users[chat_name].append(addr)
                        chat_user_perms[chat_name][addr] = {"writer":True,"configurer":False,"moderator":False,"admin":False,"banned":False,"reader":True}
                        chats_message(addr, "server", "Chat "+chat_name+" entered. ")
                elif command_name == "list_chats":
                    message = "Current chats:\n"
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
                        chats_message(addr, "server", "Chat config not available. Invalid chat name. ")
                        continue
                    if len(params)<3:
                        message = "The "+chat_name+" chat:\n"
                        for k, v in chat_configs[chat_name].items():
                            message += "is "
                            if not v:
                                message += "not "
                            message += k + "\n"
                            print("config:",message)
                            chats_message(addr, "server", message)
                        continue
                    if not chat_user_perms[chat_name][addr]["admin"]:
                        chats_message(addr, "server", "Chat config not available. You are no admin. ")
                        continue
                    message = ""
                    for exp in params[2:]:
                        if exp == "open":
                            chat_configs[chat_name]["joinable"] = True
                        elif exp == "nojoin":
                            chat_configs[chat_name]["joinable"] = False
                        elif exp == "autodel":
                            chat_configs[chat_name]["erasable"] = True
                        elif exp == "stay":
                            chat_configs[chat_name]["erasable"] = False
                        else:
                            message += "The "+exp+" option isnot supported. It was ignored. \n"
                    message += "The "+chat_name+" chat config is updated. "
                    chats_message(addr, "server", message)
                elif command_name == "user_perms":
                    if len(params)<3:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = params[1]
                    if not(chat_name in chat_users.keys()):
                        chats_message(addr, "server", "User permissions not available. Invalid chat name. ")
                        continue
                    if not(addr in chat_users[chat_name]):
                        chats_message(addr, "server", "User permissions not available. Invalid username. ")
                        continue
                    user_name = params[2]
                    user_addr = addr_of[user_name]
                    if not chat_user_perms[chat_name][addr]["admin"]:
                        chats_message(addr, "server", "Chat config not available. You are no admin. ")
                        continue
                    if len(params)<4:
                        message = "The user:\n"
                        for k, v in chat_user_perms[chat_name][user_addr].items():
                            message += "is "
                            if not v:
                                message += "not "
                            message += k + "\n"
                        continue
                    message = ""
                    for exp in params[4:]:
                        if exp == "writes":chat_configs[chat_name]["writer"] = True
                        elif exp == "nowrite":chat_configs[chat_name]["writer"] = False
                        elif exp == "confs":chat_configs[chat_name]["configurer"] = True
                        elif exp == "noconf":chat_configs[chat_name]["configurer"] = False
                        elif exp == "mods":chat_configs[chat_name]["moderator"] = True
                        elif exp == "nomod":chat_configs[chat_name]["moderator"] = False
                        elif exp == "admins":
                            chat_configs[chat_name]["admin"] = True
                            admin_num[chat_name] += 1
                        elif exp == "noadmin":
                            if admin_num[chat_name]==1:
                                message += "Removing the admin privilege isnot allowed when there is only one admin. \n"
                            else:
                                chat_configs[chat_name]["admin"] = False
                        elif exp == "banned":chat_configs[chat_name]["banned"] = True
                        elif exp == "nobanned":chat_configs[chat_name]["banned"] = False
                        elif exp == "reads":chat_configs[chat_name]["reader"] = True
                        elif exp == "noread":chat_configs[chat_name]["reader"] = False
                        else:
                            message += "The "+exp+" option isnot supported. It was ignored. \n"
                    message += "The '"+user_name+"' user in "+chat_name+" chat perms are updated. "
                    chats_message(addr, "server", message)
                elif command_name == "mute":
                    if len(params)<3:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = params[1]
                    if not(chat_name in chat_users.keys()):
                        chats_message(addr, "server", "Mute not available. Invalid chat name. ")
                        continue
                    if not(addr in chat_users[chat_name]):
                        chats_message(addr, "server", "Mute not available. Invalid username. ")
                        continue
                    user_name = params[2]
                    user_addr = addr_of[user_name]
                    if not chat_user_perms[chat_name][addr]["moderator"]:
                        chats_message(addr, "server", "Chat config noot available. You are no moderator. ")
                        continue
                    chat_configs[chat_name]["writer"] = False
                    chats_message(addr, "server", "The user '"+user_name+"' is muted. ")
                elif command_name == "cool_down":
                    if len(params)<3:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = params[1]
                    if not(chat_name in chat_users.keys()):
                        chats_message(addr, "server", "Mute not available. Invalid chat name. ")
                        continue
                    if not(addr in chat_users[chat_name]):
                        chats_message(addr, "server", "Mute not available. Invalid username. ")
                        continue
                    user_name = params[2]
                    user_addr = addr_of[user_name]
                    if not chat_user_perms[chat_name][addr]["moderator"]:
                        chats_message(addr, "server", "Chat config not available. You are no moderator. ")
                        continue
                    chat_configs[chat_name]["writer"] = True
                    chats_message(addr, "server", "The user '"+user_name+"' is cooled down. ")
                elif command_name == "userlist":
                    if len(params)<2:
                        chats_message(addr, "server", "No name specified. ")
                        continue
                    chat_name = params[1]
                    if not(chat_name in chat_users.keys()):
                        chats_message(addr, "server", "User list not available. Invalid chat name. ")
                        continue
                    message = "User list:\n"
                    for ch in chat_users[chat_name]:
                        if ch == addr:
                            message += "* "
                        message += username_of[ch] + "\n"
                    chats_message(addr, "server", message)
                else:
                    chats_message(addr, "server", "Invalid command. ")
                continue

            if addr in clients:
                if chat_user_perms[user_curr[addr]][addr]["writer"]:
                    chats_message(addr, user_curr[addr], msg)
                else:
                    chats_message(addr, "server", "Sending not available. You are no writer. ")
            else:
                user_curr[addr] = "pub"
                chat_users["pub"].append(addr)
                chat_users["server"].append(addr)
                chat_user_perms["pub"][addr] = {"writer":True,"configurer":False,"moderator":False,"admin":False,"banned":False,"reader":True}
                chat_user_perms["server"][addr] = {"writer":False,"configurer":False,"moderator":False,"admin":False,"banned":False,"reader":True}
                while lock.locked():
                    pass
                lock.acquire()
                clients.append(addr)
                unsent_messages[addr] = []
                lock.release()
                addr_of[msg] = addr
                username_of[addr] = msg
                user_chats[addr] = ["pub","server"]
        except:
            print_exc()


def broadcast(sock):
    global unsent_messages, lock
    while True:
        for client in clients:
            if len(unsent_messages[client]) > 0:
                while lock.locked():
                    pass
                lock.acquire()
                message = unsent_messages[client].pop(0)
                lock.release()
                for target in message["targets"]:
                    try:
                        sock.sendto(message["data"], eval(target))
                    except: # Aw, Man !!
                        #clients.remove(client)
                        print_exc()
                        chats_message(target, "pub",f"[SERVER] Goodbye {client}!")

def main(SERVER_PORT):
    SERVER_IP = socket.gethostbyname(socket.gethostname())

    global lock
    lock = threading.Lock()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind((SERVER_IP, SERVER_PORT))
    #print(f"Listening on {SERVER_IP}:{SERVER_PORT}")

    threading.Thread(target=receive, args=(sock, )).start()
    threading.Thread(target=broadcast, args=(sock, )).start()