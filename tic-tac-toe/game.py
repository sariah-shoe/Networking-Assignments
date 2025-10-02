import sys
from itertools import combinations

gamestate = [[0b00,0b00,0b00],
             [0b00,0b00,0b00],
             [0b00,0b00,0b00]]

magicSquare = [[4, 9, 2],
               [3, 5, 7],
               [8, 1, 6]]

xTotalMoves = []
oTotalMoves = []


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
    if(gamestate[1][0] != 0):
        print("Coordinate already claimed by the other player, choose an unclaimed coordinate")
        return([])
    return(coord)

def makeMove(coord, player):
    if player == "X":
        gamestate[coord[1]][coord[0]] = 0b01
        xTotalMoves.append(magicSquare[coord[1]][coord[0]])
        moves = xTotalMoves
    else:
        gamestate[coord[1]][coord[0]] = 0b10
        oTotalMoves.append(magicSquare[coord[1]][coord[0]])
        moves = oTotalMoves

    if len(moves) >= 3:
        for combo in combinations(moves, 3):
            if sum(combo) == 15:
                print(f"Player {player} wins!")
                sys.exit()
                
    if all(cell != 0 for row in gamestate for cell in row):
        print("It's a tie!")
        sys.exit()
        
def printGame():
    symbols = {0b00: '-', 0b01: 'x', 0b10: 'o'}
    print("  0 1 2")
    for idx, row in enumerate(gamestate):
        print(f"{idx} " + ' '.join(symbols.get(cell, '-') for cell in row))
    print()
def main():
    if (len(sys.argv) != 3):
        sys.exit("The game requires two values to run, the IP Address and Port Number")
    
    # Connecting to the server will go here eventually
    
    running = True
    xmove = ""
    xcoord = []
    omove = ""
    ocoord = []
    
    while(running):
        printGame()
        xmove = input("X make your move, submit answer in form of x,y\n")
        xcoord = verifyInput(xmove)
        makeMove(xcoord, "X")
        
        printGame()
        omove = input("O make your make, submit answer in form of x,y\n")
        ocoord = verifyInput(omove)
        makeMove(ocoord, "O")
        
        
    
if __name__ =="__main__":
    main()