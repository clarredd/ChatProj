from http.server import BaseHTTPRequestHandler, HTTPServer
from proj_client import main as cl_init, getlog, msgbuffput
from proj_server import main as msgs_init
from socket import gethostbyname, gethostname
from urllib.parse import unquote_plus as unquote

hostName = "127.0.0.1"
hostPort = 80
msgsName = gethostbyname(gethostname())
msgsPort = 1312
pids = dict()
box_buff = dict()

class TheServer(BaseHTTPRequestHandler):
    def showerror(self, err):
        with open("error.html","r") as file:
            self.wfile.write(file.read().format(err).encode("utf-8"))
    def do_GET(self):
        if "?" in self.path:
            req_name, argS = self.path.split("?")
            args = dict()
            for arg in argS.split("&"):
                key, val = arg.split("=")
                key, val = unquote(key), unquote(val)
                args[key] = val
        else:
            req_name = self.path
            args = dict()
        
        req_name = req_name.strip("/")

        if req_name in ["", "login", "send", "refresh", "updatedraft"]:
            self.send_response(200)
        else:
            self.send_response(404)

        #Location header ne radi

        self.send_header("Content-type", "text/html")
        self.end_headers()

        if req_name == "":
            with open("index.html", "rb") as file:
                self.wfile.write(file.read())
        elif req_name == "login":
            if "username" in args.keys():
                if "]:" in args["username"] or "command" in args["username"]:
                    self.showerror("That username isn't valid. ")
                elif not(args["username"] in pids.keys()):
                    pids[args["username"]] = cl_init(msgsName, msgsPort, args["username"])
                    box_buff[args["username"]] = ""
                else:
                    pass
                self.wfile.write(bytes("<script>location.href='/refresh?username="+args["username"]+"';</script>", "utf-8"))
            else:
                self.showerror("Username Not Found")
        elif req_name == "send":
            if "username" in args.keys() and "message" in args.keys() and args["username"] in pids.keys():
                msgbuffput(f'[{args["username"]}]: {args["message"].replace("command","_command")}'.encode('utf-8'), pids[args["username"]][0])
                self.wfile.write(bytes("<script>location.href='/refresh?username="+args["username"]+"';</script>", "utf-8"))
            else:
                self.showerror("Username or Message Not Found")
        elif req_name == "refresh":
            if "username" in args.keys() and args["username"] in pids.keys():
                logg = getlog(pids[args["username"]][1])
                messages = ""
                for r in logg.split("\n"):
                    messages += "<p>" + r + "</p>"
                with open("login.html", "r") as file:
                    self.wfile.write(file.read().format(messages,args["username"],"",box_buff[args["username"]]).encode("utf-8"))
            else:
                self.showerror("Username Not Found")
        elif req_name == "updatedraft":
            if "username" in args.keys() and args["username"] in pids.keys() and "draft" in args.keys():
                box_buff[args["username"]] = args["draft"]
                self.wfile.write(bytes("<script>location.href='/refresh?username="+args["username"]+"';</script>", "utf-8"))
            else:
                self.showerror("Username or Draft Not Found")
        elif req_name == "command":
            if "username" in args.keys() and args["username"] in pids.keys() and "message" in args.keys() and "command" in args.keys():
                msgbuffput("command".encode("utf-8"), pids[args["username"]][0])
                msgbuffput((args["command"]+" "+args["message"]).encode("utf-8"), pids[args["username"]][0])
                self.wfile.write(bytes("<script>location.href='/refresh?username="+args["username"]+"';</script>", "utf-8"))
            else:
                self.showerror("Username or Command Not Found")
        else:
            self.showerror("404 Not Found")

if __name__ == "__main__":
    msgs_init(msgsPort)

    server = HTTPServer((hostName, hostPort), TheServer)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
