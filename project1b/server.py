# Verify the arguments given at the beginning of the game
from itertools import combinations
import socket
import sys
import time
import random
from messaging import *

class Client:
    # Client variables
    game_id:int
    last_client_msg_id:int
    server_msg_id:int
    game_state:list[list[int]]
    name:str
    player:str
    possMoves:list[tuple]
    last_seen:time.struct_time
    last_server_packet:bytes
    xTotalMoves:list[tuple]
    oTotalMoves:list[tuple]
    
    # Initialize client with its ids, player name, server player, possible moves, and timestamp
    def __init__(self, game_id: int, message_id: int, game_state: list[list[int]], name: str):
        self.game_id = game_id
        self.last_client_msg_id = -1
        self.server_msg_id = random.randint(0,254)
        self.game_state = game_state
        self.name = name
        if(random.randint(1,2) == 1):
            self.player = "X"
        else:
            self.player = "O"
        self.possMoves = [(i, j) for i in range(3) for j in range(3)]
        self.xTotalMoves = []
        self.oTotalMoves = []
        self.last_server_packet: bytes | None = None
        self.last_seen = time.time()
    
    # Str representation of client
    def __str__(self) -> str:
        return(f"Game {self.game_id} with {self.name}, current message id is {self.message_id}, current game_state is {self.game_state}")

def verifyArgs() -> tuple:
    # If I get more arguments than expected, exit the program
    if (len(sys.argv) != 3):
        sys.exit("The game requires two values to run, the IP Address and Port Number")
     
    # If my port number isn't a number, exit the program   
    try:
        SERV_IP = sys.argv[1]
        SERV_PORT = int(sys.argv[2])
    except:
        sys.exit("Port must be a number")
    
    return(SERV_IP, SERV_PORT)

def newClientVerification(messId: int, flags: int, gameState: list[list[int]]) -> bool:
    emptyGameState = [[0b00,0b00,0b00],
                     [0b00,0b00,0b00],
                     [0b00,0b00,0b00]]
    global serverFlag
    
    if(messId != 0):
        serverFlag = possFlags[5]
        return False

    if(flags != 0):
        serverFlag = possFlags[5]
        return False
    
    if(gameState != emptyGameState):
        serverFlag = possFlags[5]
        return False
    
    serverFlag = 0
    return True

def existingClientVerification(clientMessId: int, gameState: list[list[int]], prevClient: Client) -> bool:
    global serverFlag
    
    # Validate messsage id
    if(clientMessId != prevClient.server_msg_id + 1):
        serverFlag = possFlags[5]
        return False
    
    # Find the changes the player made
    foundChanges = []
    for row in range(0,3):
        for column in range(0,3):
            if(prevClient.game_state[row][column] != gameState[row][column]):
                foundChanges.append((row, column))
    
    # Check that there is only one change
    if(len(foundChanges) != 1):
        serverFlag = possFlags[5]
        return False
    
    r, c = foundChanges[0]
    
    # Check that the correct player moved
    if(prevClient.player == "X"):
        if(gameState[r][c] != 0b10):
            serverFlag = possFlags[5]
            return False
    
    if(prevClient.player == "O"):
        if(gameState[r][c] != 0b01):
            serverFlag = possFlags[5]
            return False
        
    # Check that the move is valid, if it is remove it from my list of possible moves
    if((r,c) not in prevClient.possMoves):
        serverFlag = possFlags[5]
        return False
    else:
        prevClient.possMoves.remove((r,c))

    # Update my client object
    prevClient.last_client_msg_id = clientMessId
    prevClient.game_state = gameState
    
    # Mark as no errors and return true
    serverFlag = 0
    return True

def makeMove(client: Client) -> None:
    global serverFlag
    serverMove: tuple = random.choice(client.possMoves)
    client.possMoves.remove(serverMove)
    if(client.player == "X"):
        client.game_state[serverMove[0]][serverMove[1]] = 0b01
        client.xTotalMoves.append(serverMove)
        serverFlag = possFlags[1]
    else:
        client.game_state[serverMove[0]][serverMove[1]] = 0b10
        client.oTotalMoves.append(serverMove)
        serverFlag = possFlags[0]
        
def checkWin(client: Client) -> None:
    global serverFlag
    
    if(client.player == "X"):
        moves = client.xTotalMoves
    else:
        moves = client.oTotalMoves
        
    # Check for my win condition using the magic square, if I do win, change the flags
    if len(moves) >= 3:
        for combo in combinations(moves, 3):
            if sum(magicSquare[r][c] for (r, c) in combo) == 15:
                if client.player == "X":
                    serverFlag = possFlags[2]
                else:
                    serverFlag = possFlags[3]
    
    # If every cell is filled it's a tie
    if all(cell != 0 for row in client.game_state for cell in row):
        serverFlag = possFlags[4]

def serverMessageId(client: Client):
    # If we aren't' on the first message, ensure that we increment the clients msg id by 1
    if(client.last_client_msg_id != -1):
        client.server_msg_id = client.last_client_msg_id + 1
    # If we're larger than 255, roll over to 0
    if (client.server_msg_id > 255):
        client.server_msg_id = 0
    
def purge_inactive(now: float):
    # Go through clients and find clients that have been inactive for 300 seconds or more
    to_drop = []
    for gid, c in clients.items():
        if (now - c.last_seen) > 300:
            to_drop.append(gid)
    # Drop inactive clients
    for gid in to_drop:
        clients.pop(gid, None)

def main():
    SERV_IP, SERV_PORT = verifyArgs()
      
    # set my global variables
    global magicSquare

    magicSquare = [[4, 9, 2],
                [3, 5, 7],
                [8, 1, 6]]

    global possFlags
    possFlags = [
                    0b10000000000000, # X player to move
                    0b01000000000000, # O player to move
                    0b00100000000000, # X player wins
                    0b00010000000000, # O player wins
                    0b00001000000000, # Tie
                    0b00000100000000 # Error
                ]

    global clients
    clients = {}
    
    global serverFlag
    serverFlag = 0
    
    ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ssock.bind((SERV_IP, SERV_PORT))
    
    while True:
        # Recieve raw message and decode it
        try:
            clientRawMessage, clientAddrs = ssock.recvfrom(1024)
        except ConnectionResetError:
            # Ignore the Windows UDP reset and keep listening
            continue
        
        clientGameId, messId, flag, rawState, clientMess = decode_message(clientRawMessage)
        game_state = decode_game_state(rawState)
        
        # Set a default message for the server to send in case the branching fails
        message = encode_message(clientGameId, messId, possFlags[5], rawState, "There was an error, game ended")
        
        # Check to see if we are an exisiting client or new, do verifications
        if clientGameId in clients:
            client: Client = clients[clientGameId]
            if client.last_client_msg_id == messId:
                if client.last_server_packet is not None:
                    ssock.sendto(client.last_server_packet, clientAddrs)
                    client.last_seen = time.time()
                continue
            else:
                existingClientVerification(messId, game_state, clients[clientGameId])
        else:
            if(newClientVerification(messId, flag, game_state)):
                clients[clientGameId] = Client(clientGameId, messId, game_state, clientMess)
        
        # If an error occurs in our verification, end the game and remove the client
        if(serverFlag == possFlags[5]):
            message = encode_message(clientGameId, client.server_msg_id, possFlags[5], rawState, "There was an error, game ended")
            if(clientGameId in clients):
                clients.pop(clientGameId)
        
        # If there was no error, go forward
        else:
            # Save the client in the client object for simplicity
            client: Client = clients[clientGameId]
            
            # Increase my server_msg_id
            serverMessageId(client)
            
            # Check if the client won, if it did make the message say that they won and pop the client
            if((flag == possFlags[2] and client.player == "O") or (flag == possFlags[3] and client.player == "X")):
                message = encode_message(clientGameId, client.server_msg_id, possFlags[2], rawState, f"{client.name} wins, I lose")
                clients.pop(clientGameId)
            
            # Check if there was a tie, if there was send a message saying we tied and pop the client
            elif(flag == possFlags[4]):
                message = encode_message(clientGameId, client.server_msg_id, possFlags[4], rawState, f"{client.name} and I tie")
                clients.pop(clientGameId)
            
            # If there's an error pop the client
            elif(flag == possFlags[5]):
                message = encode_message(clientGameId, client.server_msg_id, possFlags[5], rawState, "There was an error, game ended")
                clients.pop(clientGameId)
            
            # If we recieved a flag for us to make our move, do so 
            elif(flag == possFlags[1] or flag == possFlags[0]):
                makeMove(client)
                newGameState = encode_game_state(client.game_state)
                checkWin(client)
                if(serverFlag == possFlags[2] or serverFlag == possFlags[3]):
                    message = encode_message(clientGameId, client.server_msg_id, serverFlag, newGameState, f"I win, {client.name} loses")
                    clients.pop(clientGameId)
                elif(serverFlag == possFlags[4]):
                    message = encode_message(clientGameId, client.server_msg_id, serverFlag, newGameState, f"{client.name} and I tie")
                    clients.pop(clientGameId)
                else:
                    message = encode_message(clientGameId, client.server_msg_id, serverFlag, newGameState, f"{client.name}'s turn")
                    
            # If we're on a new game and as such the flag is 0, make move if we're x, and send message informing client of their letter
            elif(flag == 0):
                if(client.player == "X"):
                    makeMove(client)
                    newGameState = encode_game_state(client.game_state)
                    message = encode_message(clientGameId, client.server_msg_id, possFlags[1], newGameState, f"I chose Xs, {client.name}'s turn")
                else:
                   message = encode_message(clientGameId, client.server_msg_id, possFlags[0], rawState, f"I chose Os, {client.name}'s turn") 
                   
            # If we get a flag we just don't recognize, send an error
            else:
                message = encode_message(clientGameId, client.server_msg_id, possFlags[5], rawState, f"{client.name} sent an invalid flag, game ended")
                clients.pop(clientGameId)
                
        # Now that we've done all our checking and our moves we have our final message, send it to the socket and wait for next message
        client.last_server_packet = message
        client.last_seen = time.time()
        ssock.sendto(message, clientAddrs)
        
        # Lastly, check if there's any games that have been around for longer than 5 minutes and purge them
        now = time.time()
        purge_inactive(now)
                
            
                    
        
    
if __name__ =="__main__":
    main()