import sys
from itertools import combinations
import random
import socket
from messaging import *

# Function to verify the user's given input, returns an empty array if invalid and an array with the x,y values if it is valid
def verifyInput(move):
    # Split the input into my two coordinates
    coord = move.split(',')
    
    # Check that I only have two coordinates
    if(len(coord) != 2):
        print("Move entered incorrectly, it should be in the format of x,y")
        return([])
    
    # Check that my coordinates are numbers
    for i in range(2):
        try:
            coord[i] = int(coord[i])
        except:
            print("Coordinate must be numbers, i.e. 0,0 not a,b")
            return([])
        
    # Check that the coordinates haven't already been claimed
    if(gamestate[coord[1]][coord[0]] != 0b00):
        print("Coordinate already claimed by the other player, choose an unclaimed coordinate")
        return([])
    
    return(coord)

# Function for the player to make their move
def makeMove(coord, player):
    global clientFlags
    
    # Change the gamestate, moves, and flags according to the user's move
    if player == "X":
        gamestate[coord[1]][coord[0]] = 0b01
        xTotalMoves.append(magicSquare[coord[1]][coord[0]])
        moves = xTotalMoves
        clientFlags = possFlags[1]
    else:
        gamestate[coord[1]][coord[0]] = 0b10
        oTotalMoves.append(magicSquare[coord[1]][coord[0]])
        moves = oTotalMoves
        clientFlags = possFlags[0]

    # Check for my win condition using the magic square, if I do win, change the flags
    if len(moves) >= 3:
        for combo in combinations(moves, 3):
            if sum(combo) == 15:
                if player == "X":
                    clientFlags = possFlags[2]
                else:
                    clientFlags = possFlags[3]
    
    # If every cell is filled it's a tie
    if all(cell != 0 for row in gamestate for cell in row):
        clientFlags = possFlags[4]

# Helper function to print the game
def printGame():
    # Map the gamestate to human readable symbols
    symbols = {0b00: '-', 0b01: 'x', 0b10: 'o'}
    print("  0 1 2")
    for idx, row in enumerate(gamestate):
        print(f"{idx} " + ' '.join(symbols.get(cell, '-') for cell in row))
    print()

# Verify the arguments given at the beginning of the game
def verifyArgs():
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
    
def main():
    # Verify and set my IP and port
    SERV_IP, SERV_PORT = verifyArgs()
    
    # set my global variables
    global gamestate 

    gamestate = [[0b00,0b00,0b00],
                [0b00,0b00,0b00],
                [0b00,0b00,0b00]]

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

    global xTotalMoves
    xTotalMoves = []

    global oTotalMoves
    oTotalMoves = []

    global gameId
    gameId = 0
    
    global clientFlags
    clientFlags = 0

    # Set my main variables
    clientSerial = 0
    running = True
    xmove = ""
    xcoord = []
    omove = ""
    ocoord = []
    gameId = random.randint(0,16777215)
    name = ""
    
    # Get the user's name, make sure its 250 characters or less
    valid = False
    while(not valid):
        name = input("Enter your name\n")
        if(len(name) > 250):
            print("Name must be 250 characters or less")
        else:
            valid = True
    
    # Initiate connection with the socket and send the starting message  
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = encode_message(gameId, 0, 0, 0, name)
    sock.sendto(message, (SERV_IP, SERV_PORT))
    
    # Enter the game loop
    while(running):
        # Make 4 attempts to recieve message from server
        for i in range(4):
            sock.settimeout(2**i)
            try:
                serverRawMessage, _ = sock.recvfrom(4096)
            except:
                if(i == 4):
                    print("Couldn't recieve a message from the server")
                    running = False
                    
        # Decode server message and gamestate
        servGameId, messId, flags, rawState, servMess = decode_message(serverRawMessage)
        gamestate = decode_game_state(rawState)
        
        # Check the gameId is valid
        if(servGameId != gameId):
            print("Game id from the server doesn't match game id for the client")
            running = False
            continue
        
        # Check that the serial id is valid
        if(clientSerial == 0):
            clientSerial = messId  
        elif(messId != (clientSerial + 1)):
            if(messId != 0):
                print("Server's message came out of order")
                running = False
                continue
        
        # If the messId is at 255 set it to 0, otherwise increase by 1
        if(messId == 255):
            clientSerial = 0
        else:
            clientSerial = messId + 1
        
        # Print the game and the server's message
        printGame()
        print(servMess)
        
        # If the server responds by telling the user they're an X, have the user make an X move
        if(flags == possFlags[0]):
            valid = False
            while(not valid):   
                xmove = input("Submit answer in form of x,y\n")
                xcoord = verifyInput(xmove)
                if(xcoord != []):
                    valid = True
            makeMove(xcoord, "X")
        
        # If the server responds by telling the user they're an O, have the user make an O move
        elif(flags == possFlags[1]):
            valid = False
            while(not valid):
                omove = input("Submit answer in form of x,y\n")
                ocoord = verifyInput(omove)
                if(ocoord != []):
                    valid = True
            makeMove(ocoord, "O")
        
        # Check win conditions and end the game if its won
        elif(flags == possFlags[2]):
            running = False
            continue
            
        elif(flags == possFlags[3]):
            running = False
            continue
            
        elif(flags == possFlags[4]):
            running = False
            continue
        
        # If there is an error end the game
        elif(flags == possFlags[5]):
            running = False
            continue
        
        # Encode the game state and message and send it to the server
        rawState = encode_game_state(gamestate)
        message = encode_message(gameId, clientSerial, clientFlags, rawState, "")
        sock.sendto(message, (SERV_IP, SERV_PORT))
    
    # When the game loop is finished, close the socket
    sock.close()
            

        
        
    
if __name__ =="__main__":
    main()