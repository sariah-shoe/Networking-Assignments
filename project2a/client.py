import sys
import json
import socket
import select
from socket import AF_INET, SOCK_STREAM

# Class to hold the client and what it does
class Client:
    # Constructor that sets name, inital subscriptions, and my users list and dictionary and my subscriptions list and dictionary
    def __init__(self, name, subscriptions):
        self.userName = name
        self.subscriptions = subscriptions
        self.users = []
        self.subscriptionsMessages = {}
        self.usersMessages = {}
        for s in self.subscriptions:
            self.subscriptionsMessages[s] = []
    
    # String form of my client
    def __str__(self):
        return(f"User {self.userName} who is subscribed to {self.subscriptions}")
    
    # Tell the client to encode a message
    def encode_message(self, action:str, target:str = "", message:str = ""):
        # If the action is connect, encode a json message with the action, user_name, and targets
        if(action == "connect"):
            encodedMessage = json.dumps({
                "action": "connect",
                "user_name": f"{self.userName}",
                "targets": self.subscriptions
            })
        # If the action is disconnect, just send the action disconnect
        elif(action == "disconnect"):
            encodedMessage = json.dumps({"action" : "disconnect"})
        # If the action is a message, encode a json message with the action, user_name, targets, and message
        elif(action == "message"):
            encodedMessage = json.dumps({
                "action" : "message",
                "user_name" : self.userName,
                "target" : target,
                "message" : message
            })
        # If my actions aren't any of those, its invalid
        else:
            print("This isn't a valid message")
            encodedMessage = ""
            
        # Return my final JSON
        return(encodedMessage)
    
    # After I send or recieve a message, make sure its in my list and dictionary
    def addUserMess(self, mess, decoded):
        # Turn it from json to a python object
        if not decoded:
            mess = json.loads(mess)
            sender = mess["user_name"]
        else:
            sender = mess["from"]
            
        # Get my sender and reciever
        reciever = mess["target"]
        
        # Check to see if I am the reciever and I've interacted with this user before
        if(reciever == self.userName and sender in self.users):
            # print(f"Appending to {sender}")
            self.usersMessages[sender].append(mess)
            
        # Check to see if I am the sender and I've interacted with this user before
        elif(reciever in self.users and sender == self.userName):
            # print(f"Appending to {reciever}")
            self.usersMessages[reciever].append(mess)
            
        # Check to see if I'm the reciever and I haven't interacted with this user before
        elif(reciever == self.userName and sender not in self.users):
            # print(f"Creating and appending to {sender}")
            self.users.append(sender)
            self.usersMessages[sender] = []
            self.usersMessages[sender].append(mess)
            
        # Check to see if I'm the sender and I haven't interacted with this user before
        elif(sender == self.userName and reciever not in self.users):
            # print(f"Creating and appending to {reciever}")
            self.users.append(reciever)
            self.usersMessages[reciever] = []
            self.usersMessages[reciever].append(mess)
            
        # If none of these conditions apply, the message wasn't meant for me, ignore it
        else:
            # print("No match found")
            pass
    
    # After I send or recieve a message, make sure its in my room list and dictionary
    def addRoomMess(self, mess, decoded):
        # Decode the json
        if not decoded:
            mess = json.loads(mess)
            sender = mess["user_name"]
        else:
            sender = mess["from"]
            
        # Get my sender and reciever
        reciever = mess["target"]
        
        # Checks to see if it's a subscription I'm subscribed to
        if(reciever in self.subscriptions):
            # print(f"Appending to {reciever}")
            self.subscriptionsMessages[reciever].append(mess)
            
        # Checks to see if I'm the sender and I've not seen the subscription before
        elif(sender == self.userName and reciever not in self.subscriptions):
            # print(f"Creating and appending to {reciever}")
            self.subscriptions.append(reciever)
            self.subscriptionsMessages[reciever] = []
            self.subscriptionsMessages[reciever].append(mess)
           
    # Print out the history
    def printHistory(self, nameType, name):
        if nameType == "user":
            if name in self.users:
                for mess in self.usersMessages[name]:
                    try:
                        sender = mess["user_name"]
                    except:
                        sender = mess["from"]
                    message = mess["message"]
                    print(f"{sender}\t {message}\n")
            else:
                print(f"It looks like you don't have any history with user {name}")
        elif nameType == "room":
            if name in self.subscriptions:
                for mess in self.subscriptionsMessages[name]:
                    try:
                        sender = mess["user_name"]
                    except:
                        sender = mess["from"]
                    message = mess["message"]
                    print(f"{sender}\t {message}")
            else:
                print(f"It looks like you don't have any history with room {name}")
                
    # Handles server information
    def decodeServer(self, raw):
        # Decode
        pkt = json.loads(raw)
        
        # Check if we're chat info
        status = pkt.get("status")
        if(status == "chat"):
            # Go through each new message
            for one in pkt.get("history", []):
                # Check to see if it has an @ or a # so we know if its a user or a room and add it accordingly
                if("#" in one.get("target", "")):
                    self.addRoomMess(one, True)
                elif("@" in one.get("target","") or "@" in one.get("from","")):
                    self.addUserMess(one, True)
        # Check if the server disconnected, if it did, go away
        elif(status == "disconnect"):
            print("Server dissapeared. Goodbye.")
            sys.exit(0)
        
        # Check if the server sent an error, print it out
        elif(status == "error"):
            print(f'The server came across an error:\n {pkt["message"]}')  
    
# Verify the arguments given at the beginning of the chat
def verifyArgs():
    # If I get more arguments than expected, exit the program
    if (len(sys.argv) != 3):
        sys.exit("The chat requires two values to run, the IP Address and Port Number")
     
    # If my port number isn't a number, exit the program   
    try:
        SERV_IP = sys.argv[1]
        SERV_PORT = int(sys.argv[2])
    except:
        sys.exit("Port must be a number")
    
    return(SERV_IP, SERV_PORT)

# Error printing for server
def print_error(e, f="UNKNOWN"):
    print("Error in %s!" % (f))
    print(e)
    print(type(e))

# Send data through socket
def send_json(tcp_sock, data):
    frame = (data + "\n").encode("utf-8")
    tcp_sock.sendall(frame)
    
def drain_sock(sock, client):
    # Read and handle all currently available data on the socket
    try:
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                print("Server closed connection.")
                sys.exit(0)
            for line in filter(None, chunk.decode("utf-8").splitlines()):
                client.decodeServer(line)
    except BlockingIOError:
        return
    
# Validate the name of a user or of a room
def validateName(nameType, name):
    # Normalize the name
    name = name.lower()
    name = name.strip()
    
    # Check number of bytes
    nameNumBytes = len(name.encode('utf-8'))
    if(nameNumBytes > 60):
        print("Name must be 60 bytes or less")
        return(name, False)
    
    # If its a valid user, return the cleaned name and true
    if(nameType == "user"):
        return(f"@{name}", True)
    
    # If its a valid room, return the cleaned name and true
    elif(nameType == "room"):
        return(f"#{name}", True)
    
    # If its some other type, just return an empty string and false
    else:
        return("", False)

# Validate the message being send
def validateMess(mess):
    # Check # of byes is < 3800
    messNumBytes = len(mess.encode('utf-8'))
    if(messNumBytes > 3800):
        return False
    else:
        return True
    
def show_menu():
    print("1. Send message to user")
    print("2. Send message to room")
    print("3. See messages from users")
    print("4. See messages in rooms")
    print("5. Disconnect")
    
def printPrompt():
    prompt = "> "
    print(prompt, end="", flush=True)
    
def menu_loop(tcp_sock, client):
    states = ["MENU", "USER_TARGET", "ROOM_TARGET", "PICK_USER", "PICK_ROOM", "USER_MSG", "ROOM_MSG"]
    state = states[0]
    pending = {}
    
    show_menu()
    printPrompt()
    
    while True:
        rlist, _, _ = select.select([tcp_sock, sys.stdin], [], [])
        
        # If we get server data
        if tcp_sock in rlist:
            drain_sock(tcp_sock, client)
            printPrompt()
        
        # If we get user input
        if sys.stdin in rlist:
            # Get my input
            line = sys.stdin.readline()
            if not line:
                continue
            line = line.rstrip("\n")
            
            # If I'm in the menu
            if state == states[0]:
                # Make sure I got a number
                try:
                    line = int(line)
                except:
                    print("Response must be a number")
                    continue
                
                # Send message to user
                if line == 1:
                    state = states[1]
                    print("Who would you like to send a message to? \n")
                    printPrompt()
                
                # Send message to room
                elif line == 2:
                    state = states[2]
                    print("Which room would you like to send a message to? \n")
                    printPrompt()
                
                # Read messages from users   
                elif line == 3:
                    state = states[3]
                    for i in range(len(client.users)):
                        print(f"{i}. {client.users[i]}")
                    print(f"{len(client.users)}. Return to main menu")
                    printPrompt()
                
                # Read messages from rooms
                elif line == 4:
                    state = states[4]
                    for i in range(len(client.subscriptions)):
                        print(f"{i}. {client.subscriptions[i]}")
                    print(f"{len(client.subscriptions)}. Return to main menu")
                    printPrompt()
                
                # Disconnect
                elif line == 5:
                    bye = client.encode_message("disconnect")
                    send_json(tcp_sock, bye)
                    return
                
                # Invalid action
                else:
                    print(f"{line} is not a valid action, please choose a number between 1-5")
                    show_menu()
                    printPrompt()
            
            # If I'm waiting for user name to send to        
            elif state == states[1]:
                # Validate the name of the user
                clean, ok = validateName("user", line)
                if not ok:
                    print(f"{clean} is an invalid user. Try again")
                else:
                    # Add the target to pending and prepare to get the message to send
                    pending["target"] = clean
                    state = states[5]
                    print("What message would you like to send?")
                printPrompt()
              
            # If I'm waiting for room name to send to  
            elif state == states[2]:
                # Validate the name of the room
                clean, ok = validateName("room", line)
                if not ok:
                    print(f"{clean} is an invalid room. Try again")
                else:
                    # Add the target to pending and prepare to get the message
                    pending["target"] = clean
                    state = states[6]
                    print("What message would yu like to send?")
                printPrompt()
            
            # If I'm waiting for a user to read from    
            elif state == states[3]:
                # Make sure its a number
                try:
                    idx = int(line)
                except ValueError:
                    print("Please enter a number.")
                    printPrompt()
                    continue
                
                # Display user or change to menu
                if idx == len(client.users):
                    state = states[0]
                elif 0 <= idx < len(client.users):
                    client.printHistory("user", client.users[idx])
                    state = states[0]
                else:
                    print("Out of range")
                
                # Print menu   
                show_menu()
                printPrompt()
            
            # If I'm waiting for a room to read from
            elif state == states[4]:
                # Make sure its a number
                try:
                    idx = int(line)
                except ValueError:
                    print("Please enter a number.")
                    printPrompt()
                    continue
                
                #Display room or change to menu
                if idx == len(client.subscriptions):
                    state = states[0]
                elif 0 <= idx < len(client.subscriptions):
                    client.printHistory("room", client.subscriptions[idx])
                    state = states[0]
                else:
                    print("Out of range.")
                
                # Print menu
                show_menu()
                printPrompt()
            
            # If I'm waiting for a message to a user    
            elif state == states[5]:
                # Validate message
                if not validateMess(line):
                    print("Message too long. Try again:")
                    printPrompt()
                    continue
                
                # Encode message and add it to my messages
                pkt = client.encode_message("message", pending["target"], line)
                client.addUserMess(pkt, False)
                
                # Send through sock, drain, and clear pending
                send_json(tcp_sock, pkt)
                drain_sock(tcp_sock, client)
                pending.clear()
                
                # Return to the main menu
                state = states[0]
                show_menu()
                printPrompt()
            
            # If I'm waiting for a message to a room   
            elif state == states[6]:
                # Validate message
                if not validateMess(line):
                    print("Message too long. Try again:")
                    printPrompt()
                    continue
                
                # Encode message and add it to my messages
                pkt = client.encode_message("message", pending["target"], line)
                client.addRoomMess(pkt, False)
                
                # Send through sock, drain, and clear pending
                send_json(tcp_sock, pkt)
                drain_sock(tcp_sock, client)
                pending.clear()
                state = states[0]
                
                # Return to main menu
                show_menu()
                printPrompt()      
    
def main():
    # Check my arguments
    SERV_IP, SERV_PORT = verifyArgs()
    
    # Create a socket to connect to server
    try:
        tcp_sock = socket.socket(AF_INET, SOCK_STREAM)
    except Exception as e:
        print_error(e, "socket")
        sys.exit(1)
        
    # Attempt to connect to server
    try:
        tcp_sock.connect((SERV_IP, SERV_PORT))
    except Exception as e:
        print_error(e, "connect")
        sys.exit(1)
        
    # Initialize user name, strip and lower it, check that it has valid length
    valid = False
    while (not valid):
        name = input("Enter your name\n")
        name, valid = validateName("user", name)
    
    # Initialize subscriptions, strip and lower each one, and check that it has valid length
    valid = False
    while(not valid):
        rawSubscriptions = input("Enter the channels you would like to subscribe to. Enter them with commas between each subscription, for example 'networking, music'\n")
        raw_list = rawSubscriptions.split(",")
        subscriptions = []
        all_valid = True
        for s in raw_list:
            cleaned, sValid = validateName("room", s)
            if(sValid):
                subscriptions.append(cleaned)
            else:
                all_valid = False
        if all_valid:
            valid = True
    
    # Now that I've validated, start my client
    thisClient = Client(name, subscriptions)
    
    tcp_sock.setblocking(False)
    
    # Send initial message
    hello = thisClient.encode_message("connect")
    send_json(tcp_sock, hello)
    
    # Read initial history
    drain_sock(tcp_sock, thisClient)
    
    # Have the select-based menu loop handle from here
    try:
        menu_loop(tcp_sock, thisClient)
    except KeyboardInterrupt:
        try:
            bye = thisClient.encode_message("disconnect")
            send_json(tcp_sock, bye)
        except Exception:
            pass
    finally:
        try:
            tcp_sock.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()