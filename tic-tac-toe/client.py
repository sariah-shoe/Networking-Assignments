import sys
from itertools import combinations
import random
import socket
from messaging import *

def verifyInput(move):
    coord = move.split(',')
    if(len(coord) != 2):
        print("Move entered incorrectly, it should be in the format of x,y")
        return([])
    for i in range(2):
        try:
            coord[i] = int(coord[i])
        except:
            print("Coordinate must be numbers, i.e. 0,0 not a,b")
            return([])
    if(gamestate[coord[1]][coord[0]] != 0):
        print("Coordinate already claimed by the other player, choose an unclaimed coordinate")
        return([])
    return(coord)

def makeMove(coord, player):
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

    if len(moves) >= 3:
        for combo in combinations(moves, 3):
            if sum(combo) == 15:
                if player == "X":
                    clientFlags = possFlags[2]
                else:
                    clientFlags = possFlags[3]
                
    if all(cell != 0 for row in gamestate for cell in row):
        print("It's a tie!")
        clientFlags = possFlags[4]
        
def printGame():
    symbols = {0b00: '-', 0b01: 'x', 0b10: 'o'}
    print("  0 1 2")
    for idx, row in enumerate(gamestate):
        print(f"{idx} " + ' '.join(symbols.get(cell, '-') for cell in row))
    print()
    
def verifyArgs():
    if (len(sys.argv) != 3):
        sys.exit("The game requires two values to run, the IP Address and Port Number")
        
    try:
        SERV_IP = sys.argv[1]
        SERV_PORT = int(sys.argv[2])
    except:
        sys.exit("Port must be a number")
    
    return(SERV_IP, SERV_PORT)
    
def main():
    SERV_IP, SERV_PORT = verifyArgs()
    
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

    global clientSerial
    clientSerial = 0

    global clientFlags
    clientFlags = 0

    
    running = True
    xmove = ""
    xcoord = []
    omove = ""
    ocoord = []
    gameId = random.randint(0,16777215)
    name = ""
    
    valid = False
    while(not valid):
        name = input("Enter your name\n")
        if(len(name) > 250):
            print("Name must be 250 characters or less")
        else:
            valid = True
            
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = encode_message(gameId, 0, 0, 0, name)
    sock.sendto(message, (SERV_IP, SERV_PORT))
    
    while(running):
        serverRawMessage, _ = sock.recvfrom(4096)
        servGameId, messId, flags, rawState, servMess = decode_message(serverRawMessage)
        gamestate = decode_game_state(rawState)
        
        if(servGameId != gameId):
            print("Game id from the server doesn't match game id for the client")
            running = False
          
        if(clientSerial == 0):
            clientSerial = messId  
        elif(messId != (clientSerial + 1)):
            if(messId != 0):
                print("Server's message came out of order")
                running = False
                
        if(messId == 255):
            clientSerial = 0
        else:
            clientSerial = messId + 1
        
        printGame()
        print(servMess)
        
        if(flags == possFlags[0]):
            valid = False
            while(not valid):   
                xmove = input("Submit answer in form of x,y\n")
                xcoord = verifyInput(xmove)
                if(xcoord != []):
                    valid = True
            makeMove(xcoord, "X")
        
        elif(flags == possFlags[1]):
            valid = False
            while(not valid):
                omove = input("Submit answer in form of x,y\n")
                ocoord = verifyInput(omove)
                if(ocoord != []):
                    valid = True
            makeMove(ocoord, "O")
        
        elif(flags == possFlags[2]):
            running = False
            
        elif(flags == possFlags[3]):
            running = False
            
        elif(flags == possFlags[4]):
            running = False
            
        elif(flags == possFlags[5]):
            print("There was an error with the server")
            running = False
            
        rawState = encode_game_state(gamestate)
        message = encode_message(gameId, clientSerial, clientFlags, rawState, "")
        sock.sendto(message, (SERV_IP, SERV_PORT))
    sock.close()
            

        
        
    
if __name__ =="__main__":
    main()