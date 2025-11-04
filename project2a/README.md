# TCP Chat Client

## How to Start
Needs to be run on Linux (WSL) or Mac for select to work properly.
Run "python client.py server.example.com port#"
To chat with class server, set compnet.cs.du.edu as the server and 7775 as the port

## Chat UI
The user will be prompted with 5 options
1. Send message to user
2. Send message to room
3. See messages from users
4. See messages in rooms
5. Disconnect

To select an option the user types the number of the option and pushes enter.

### Send Message to User
The user types in the username of the user they want to message.
They are then prompted to send a message. 
The message is sent to the server and added to the history logs.

### Send Message to Room
The user types in the username of the room they want to message. This can be one they are already subscribed to or a new room.
They are then prompted to send a message.
The message is sent to the server and added to the history logs.

### See Messages From Users
The user is given a list of users they have sent messages to or recieved messages from.
They select the user and the messages are displayed.

### See Messages in Rooms
The user is given a list of rooms they have subscribed to or sent messages to.
They select the room and the messages are displayed.

### Disconnect
The user can disconnect by pushing 5. They can also ctrl-c to quit.