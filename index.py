from http.server import BaseHTTPRequestHandler, HTTPServer
from proj_client import main as cl_init, getlog, msgbuffput
from proj_server import main as msgs_init
from socket import gethostbyname, gethostname

hostName = "127.0.0.1"
hostPort = 80
msgsName = gethostbyname(gethostname())
msgsPort = 1312
pids = dict()

class TheServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if "?" in self.path:
            req_name, argS = self.path.split("?")
            args = dict()
            for arg in argS.split("&"):
                key, val = arg.split("=")
                args[key] = val
        else:
            req_name = self.path
            args = dict()
        
        req_name = req_name.strip("/")

        if req_name in ["", "login", "send", "refresh"]:
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
            pids[args["username"]] = cl_init(msgsName, msgsPort, args["username"])
            self.wfile.write(bytes("<script>location.href='/refresh?username="+args["username"]+"';</script>", "utf-8"))
        elif req_name == "send":
            msgbuffput(args["message"], pids[args["username"]][0])
            self.wfile.write(bytes("<script>location.href='/refresh?username="+args["username"]+"';</script>", "utf-8"))
        elif req_name == "refresh":
            logg = getlog(pids[args["username"]][1])
            messages = ""
            for r in logg.split("\n"):
                messages += "<p>" + r + "</p>"
            with open("login.html", "r") as file:
                self.wfile.write(file.read().format(messages,args["username"]).encode("utf-8"))
        else:
            self.wfile.write(bytes("404 Not Found", "utf-8"))

if __name__ == "__main__":
    msgs_init(msgsPort)

    server = HTTPServer((hostName, hostPort), TheServer)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
