import pygame
import random
import librosa
import os
import sox
from pydub import AudioSegment
import pygame_gui
import copy, time

numberOfPieces = 12
piecePerSong = 2
mainPath = os.getcwd()
tempPath = mainPath + '/tempFolder' 

##############################################
# Get song pieces
##############################################
# The use of AudioSegment is cited from https://github.com/jiaaro/pydub
def getRandomPiece(song):
    # song is an AudioSegment object
    tempSong = song
    pieceLength = 4*1000
    os.chdir(tempPath)
    for _ in range(2):
        startIndex = random.randrange(0, len(tempSong)-pieceLength)
        endIndex = startIndex + pieceLength
        songPiece = tempSong[startIndex:endIndex]
        songPiece.export(f"{startIndex},{endIndex}.wav",format='wav')
    
def getRandomSong(numberOfSongs, genre):
    path = mainPath + '/songs/' + genre
    allSongs = os.listdir(path)  # lsit of songname
    songList = []
    count = 0
    while count < numberOfSongs:
        index = random.randrange(0, len(allSongs))
        if allSongs[index].endswith('.wav'):
            songList.append(allSongs[index])
            count += 1
    return songList # a list of songnames

def getCollectionOfPieces(genre):
    os.mkdir(tempPath)
    numberOfSongs = numberOfPieces//piecePerSong # pick two pieces from each song
    songList = getRandomSong(numberOfSongs, genre)
    for songName in songList:   # song is absolute path of that song
        os.chdir(mainPath +'/songs/' + genre)
        song = AudioSegment.from_wav(songName)
        getRandomPiece(song)

##############################################
# Helper Functions (For Maze)
##############################################
def getAvailableDirections(path, currentIndex):
    currentNode = path[currentIndex]
    nextNode = path[currentIndex+1]

    def checkDirections(node1, node2):
        availableDirections = []

        if node1[0] == node2[0]:
            if node1[1] > node2[1]:
                availableDirections.append((0, +1))
            else:
                availableDirections.append((0, -1))
        if node1[1] == node2[1]:
            if node1[0] > node2[0]:
                availableDirections.append((+1, 0))
            else:
                availableDirections.append((-1, 0))
    
        return availableDirections

    d1 = checkDirections(nextNode, currentNode)
    if currentIndex != 0:
        preNode = path[currentIndex-1]
        d2 = checkDirections(preNode, currentNode)
        return d1 + d2
    
    return d1

# The use of librosa is cited from https://librosa.github.io/librosa/tutorial.html#quickstart
def getSinglePieceLengths(path):
    os.chdir(path)
    y, sr = librosa.load('output.wav')
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr) 
    singlePieceLengths = [int((beat_times[i]-beat_times[i-1])*(len(beat_times)*5)) for i in range(1, len(beat_times))]
    # every song piece has 20s
    singlePieceLengths.insert(0, beat_times[0]*(len(beat_times)))
    return singlePieceLengths

def lineSegmentIntersect(start1, end1, start2, end2):
    (x1, y1), (x2, y2) = start1, end1
    (x3, y3), (x4, y4) = start2, end2
    # first find the intersection point
    xDifferences, yDifferences = (x2-x1, x4-x3), (y2-y1, y4-y3)
    # parallel
    if (xDifferences[0] == yDifferences[1]):
        intersectionPoint = (x1, y3)
        if ((min(x3, x4) <= x1 <= max(x3, x4)) and (min(y1, y2) <= y3 <= max(y1, y2))):
            return True
    elif (yDifferences[0] == xDifferences[1]):
        intersectionPoint = (x3, y1)
        if ((min(x1, x2) <= x3 <= max(x1, x2)) and (min(y3, y4) <= y1 <= max(y3, y4))):
            return True
    else:
        return False

# find the closest point on the solutionPath to the blank area
def getStartPos(positions, bound):
    distances = dict()
    distanceList = []
    xBounds = (bound[0], bound[0]+rectW)
    yBounds = (bound[1], bound[1]+rectH)
    for (x, y) in positions:
        if abs(x-xBounds[0]) < abs(x-xBounds[1]): closerX = xBounds[0]
        else: closerX = xBounds[1]
        if abs(y-yBounds[0]) < abs(y-yBounds[1]): closerY = yBounds[0]
        else: closerY = yBounds[1]
        distance = ((x-closerX)**2+(y-closerY)**2)**0.5
        distances[distance] = (x, y, closerX, closerY)
        distanceList.append(distance)
    (minX, minY, closerX, closerY) = distances[min(distanceList)]
    if xBounds[0] <= minX <= xBounds[1]: 
        return [(minX, minY), (minX, closerY)]
    elif yBounds[0] <= minY <= yBounds[1]: 
        return [(minX, minY), (closerX, minY)]
    else:
        return [(minX, minY), (minX, closerY), (closerX, closerY)]

def isoverlapping(target, lst):
    if lst == []: return False
    (x1, y1) = (target[0]+Bubble.r, target[1]+Bubble.r)
    for (x2, y2) in lst:
        (x2, y2) = (x2+Bubble.r, y2+Bubble.r)
        if ((x1-x2)**2+(y1-y2)**2)**0.5 <= 2*Bubble.r: return True 
    return False

# solve the maze until we get a maze with blank area
def findBestMaze(mazeMaker):
    findBestMaze = False
    bounds = None
    maze = None
    while not findBestMaze:
        print("Come on don't stuck here")
        (moves, maze) = mazeMaker.solve(checkConstraints=True)
        if maze == None:
            pass     
        bounds = maze.checkBlankness()
        if bounds != None:
            findBestMaze = True
    return bounds, maze

def findBestSubMaze(subMazeMaker):
    findBestSubMaze = False
    subMaze = None 
    while not findBestSubMaze:
        (moves, subMaze) = subMazeMaker.solve(checkConstraints=True)
        if subMaze != None:
            findBestSubMaze = True
    return subMaze

##############################################
# Body Part
##############################################
# The use of pygame gets reference to https://pythonprogramming.net/pygame-python-3-part-1-intro/ 
# init the game 
pygame.init()

black = (0,0,0)
white = (255,255,255)
brightYellow = (252, 232, 3)
darkYellow = (252, 219, 3)
green = (33, 143, 80)
red = (242, 12, 0)
pink = (252, 3, 148)

LEFT = 1
RIGHT = 3

genreList = ['rock', 'country', 'pop', 'classical', 'Select Genre', 
            'jazz', 'blues', 'hiphop', 'metal']
musicGenre = None
genreDictionary = dict()
allBubbles = None
selectedSongList = []

displayW = 800
displayH = 600
rectW = displayW//4 + 1
rectH = displayH//4 + 1
buttonW, buttonH = displayW/6, displayH/12
defaultDirections = [(+1, 0), (0, +1), (-1, 0), (0, -1)] # Down, Right, Left, Up
margin = 10

mainDisplay = pygame.display.set_mode((displayW, displayH))
pygame.display.set_caption('Flash Marshmallow')

##############################################
# Classes (for App)
# Reference to https://python-forum.io/Thread-PyGame-User-Interface
##############################################
class Button(object):
    mouse = pygame.mouse.get_pos()

    def __init__(self, msg, x, y, action=None):
        self.msg = msg
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, buttonW, buttonH)
        self.action = action 
    
    def get_pressed(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
            if self.rect.collidepoint(event.pos):
                self.action()
    
    def draw(self):
        if ((self.x+buttonW > Button.mouse[0] > self.x) and 
            (self.y+buttonH > Button.mouse[1] > self.y)):
            pygame.draw.rect(mainDisplay, darkYellow, (self.x, self.y, buttonW, buttonH))        
        else:
            pygame.draw.rect(mainDisplay, brightYellow, (self.x, self.y, buttonW, buttonH))
        
        textSurf, textRect = createText(self.msg, black, 20)
        textRect.center = (self.x+(buttonW/2), self.y+(buttonH/2))
        mainDisplay.blit(textSurf, textRect)


class Bubble(Button):
    images = [f'b{i+1}.png' for i in range(12)]
    r = 40
    isSelected = False
    selected = None
    
    def __init__(self, pos, image, music):
        self.pos = pos # a tuple 
        self.image = image
        self.music = music
        self.rect = pygame.Rect(self.pos[0], self.pos[1], 2*Bubble.r, 2*Bubble.r)
        self.action = self.playMusic
        
    
    def get_rightPressed(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == RIGHT:
            if self.rect.collidepoint(event.pos):
                Bubble.isSelected = True
                Bubble.selected = self

    @staticmethod
    def createBubbles(number, songPieces):
        bubbles = []
        positions = []
        count = 0
        while count < number:
            left = random.randint(displayW//14, 9*displayW//14-2*Bubble.r)
            top = random.randint(displayH//14, 13*displayH//14-2*Bubble.r)
            if not isoverlapping((left, top), positions):
                positions.append((left, top))
                image = random.choice(Bubble.images)
                bubbles.append(Bubble((left, top), image, songPieces[count]))
                count += 1
        return bubbles 

    @staticmethod 
    def drawBubbles(bubbleList):
        for bubble in bubbleList:
            image = pygame.image.load(bubble.image)
            image = pygame.transform.scale(image, (Bubble.r*2, Bubble.r*2))
            mainDisplay.blit(image, [bubble.pos[0], bubble.pos[1]])
    
    def playMusic(self):
        os.chdir(tempPath)
        bubbleMusic = pygame.mixer.Sound(self.music)
        bubbleMusic.play()

##############################################
# Helper Functions (For App)
##############################################
def createText(text, color, size, bold=False):
    textFont = pygame.font.SysFont("georgia", size, bold=bold)
    textSurface = textFont.render(text, True, color)
    return textSurface, textSurface.get_rect() 

##############################################
# App
##############################################
def runApp():
    def starterMenu():
        os.chdir(mainPath)
        button = Button('Music Mixer', displayW/2.5, 2*displayH/3, helpPage)
        
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                button.get_pressed(event)
                
            bgImg = pygame.image.load('bg(startermenu).jpg').convert()
            bgImg = pygame.transform.scale(bgImg, (800, 600))
            mainDisplay.blit(bgImg, [0, 0])
            button.draw()
            
            textSurf, textRect = createText("Flash Marshmallow", brightYellow, 80)
            textRect.center = (displayW/2, displayH/3)
            mainDisplay.blit(textSurf, textRect)
            
            pygame.display.update()

    def helpPage():
        button1 = Button('Continue', displayW/6, 4*displayH/5, selectGenre)
        button2 = Button('Go Back', 5*displayW/6-buttonW, 4*displayH/5, starterMenu)

        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                button1.get_pressed(event)
                button2.get_pressed(event)

            helpMsg = [
            'Help Page',
            'Welcome to Flash Marshmallow! In this game, you can', 
            'create your own maze game and share with your friends.',
            'To begin, select a music genre and five bubbles. Each',
            'bubble has a song piece related to it. Left click the', 
            'bubble to listen to the music, and right click to select',
            "it. Let's do it!"
            ]
            bgImg = pygame.image.load('bg(helpPage).jpg').convert()
            bgImg = pygame.transform.scale(bgImg, (800, 600))
            mainDisplay.blit(bgImg, [0, 0])
            button1.draw()
            button2.draw()
            for i in range(len(helpMsg)):
                msg = helpMsg[i]
                textSurf, textRect = createText(msg, brightYellow, 30)
                textRect.center = (displayW/2, (i+1)*displayH/10)
                mainDisplay.blit(textSurf, textRect)
            # button to go back to the starter menue
            pygame.display.update()

    def loadGenres():
        for i in range(3):
            for j in range(3):
                rect = pygame.Rect(120+j*200, 70+i*160, 150, 120)
                genreDictionary[genreList[3*i+j]] = rect
            else: 
                genreDictionary[genreList[i]] = None

    def selectGenre():
        bgImg = pygame.image.load('musicGenre.png').convert()
        bgImg = pygame.transform.scale(bgImg, (600, 500))
        loadGenres()

        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos() 
                    for genre in genreDictionary:
                        rect = genreDictionary[genre] 
                        if  ((rect != None) and (rect.collidepoint(pos))):
                            musicGenre = genre
                            textSurf, textRect = createText(f"You select {musicGenre}", brightYellow, 40, bold=True)
                            textRect.center = (displayW/2, displayH/2)
                            mainDisplay.blit(textSurf, textRect)
                            pygame.display.update()
                            buildMusic(musicGenre)  
            
            mainDisplay.fill(black)
            mainDisplay.blit(bgImg, [100, 50])
            genreNames = [(createText(genreList[i], pink, 30, True)) 
                        for i in range(len(genreDictionary))] 
            for i in range(3):
                for j in range(3):
                    genreNames[3*i+j][1].center = (200*(j+1), 135+i*165)
                    mainDisplay.blit(genreNames[3*i+j][0], genreNames[3*i+j][1])
            
            pygame.display.update()

    # The use of pygame_gui is cited from https://github.com/MyreMylar/pygame_gui
    def buildMusic(musicGenre):
        getCollectionOfPieces(musicGenre) 
        allSongPieces = os.listdir(tempPath) 
        print(allSongPieces)
        allBubbles = Bubble.createBubbles(numberOfPieces, allSongPieces)
        manager = pygame_gui.UIManager((displayW, displayH))
        rect = pygame.Rect(displayW/14, displayH/14, 8*displayW/14, 12*displayH/14)

        selectionButton1 = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(9.5*displayW/14, 2*displayH/14, 4.5*displayH/14, 2*displayH/14),
            text='Select by right clicking', manager=manager)
        selectionButton2 = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(9.5*displayW/14, 5*displayH/14, 4.5*displayH/14, 2*displayH/14),
            text='Are you sure?', manager=manager)
        yesButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(9.5*displayW/14, 8*displayH/14, 1.5*displayH/14, 1*displayH/14),
            text='Yes', manager=manager)
        noButton = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(11.5*displayW/14, 8*displayH/14, 1.5*displayH/14, 1*displayH/14),
            text='No', manager=manager)

        done = False
        while not done:
    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True

                for bubble in allBubbles:
                    bubble.get_pressed(event)
                    bubble.get_rightPressed(event)

                if event.type == pygame.USEREVENT:
                    if event.user_type == 'ui_button_pressed':
                        if Bubble.isSelected == True:    
                            if event.ui_element == yesButton:
                                allBubbles.remove(Bubble.selected)
                                selectMusic(Bubble.selected)
                            if event.ui_element == noButton: 
                                Bubble.selected = None
                                Bubble.isSelected = False
                
                manager.process_events(event)
            
            os.chdir(mainPath)
            mainDisplay.fill(black)
            pygame.draw.rect(mainDisplay, white, rect, 3)
            manager.draw_ui(mainDisplay)
            Bubble.drawBubbles(allBubbles)
            if Bubble.isSelected == True:
                pygame.draw.rect(mainDisplay, brightYellow, Bubble.selected.rect, 2)

            pygame.display.update()

    def selectMusic(selected):
        selectedSongList.append(selected.music)
        Bubble.isSelected = False
        Bubble.selected = None
        if len(set(selectedSongList)) > 4:
            for songName in os.listdir(tempPath):
                if songName not in selectedSongList:
                    os.remove(tempPath + '/' + songName)
            mixMusic()

    # The use of sox to mix music is cited from https://pysox.readthedocs.io/en/latest/api.html#module-sox.combine
    def mixMusic():
        os.chdir(tempPath)
        songList = os.listdir(tempPath)

        cbn = sox.Combiner()
        cbn.pitch(3.0)
        cbn.convert(samplerate=8000)
        cbn.build(songList, 'output.wav', 'concatenate')
        
        runMaze()

    try:
        fileNames = os.listdir(tempPath)
        for fileName in fileNames:
            os.remove(tempPath + '/' + fileName)
        os.rmdir(tempPath) 
    except:
        pass

    starterMenu()

##############################################
# Make and Play Maze
##############################################
def runMaze():

##############################################
# Generic backtracking-based puzzle solver
# Cited from https://www.cs.cmu.edu/~112/notes/notes-recursion-part2.html#whatIsBacktracking
##############################################

    class BacktrackingPuzzleSolver(object):
        def solve(self, checkConstraints=True, printReport=False):
            self.moves = [ ]
            self.states = set()
            # If checkConstraints is False, then do not check the backtracking
            # constraints as we go (so instead do an exhaustive search)
            self.checkConstraints = checkConstraints
            # Be sure to set self.startArgs and self.startState in __init__
            self.startTime = time.time()
            self.solutionState = self.solveFromState(self.startState)
            self.endTime = time.time()
            if (printReport): self.printReport()
            return (self.moves, self.solutionState)

        def printReport(self):
            print()
            print('***********************************')
            argsStr = str(self.startArgs).replace(',)',')') # remove singleton comma
            print(f'Report for {self.__class__.__name__}{argsStr}')
            print('checkConstraints:', self.checkConstraints)
            print('Moves:', self.moves)
            print('Solution state: ', end='')
            if ('\n' in str(self.solutionState)): print()
            print(self.solutionState)
            print('------------')
            print('Total states:', len(self.states))
            print('Total moves: ', len(self.moves))
            millis = int((self.endTime - self.startTime)*1000)
            print('Total time:  ', millis, 'ms')
            print('***********************************')

        def solveFromState(self, state):
            if state in self.states:
                # we have already seen this state, so skip it
                return None
            self.states.add(state)
            if self.isSolutionState(state):
                # we found a solution, so return it!
                return state
            else:
                for move in self.getLegalMoves(state):
                    # 1. Apply the move
                    childState = self.doMove(state, move)
                    # 2. Verify the move satisfies the backtracking constraints
                    #    (only proceed if so)
                    if ((self.stateSatisfiesConstraints(childState)) or
                        (not self.checkConstraints)):
                        # 3. Add the move to our solution path (self.moves)
                        self.moves.append(move)
                        # 4. Try to recursively solve from this new state
                        result = self.solveFromState(childState)
                        # 5. If we solved it, then return the solution!
                        if result != None:
                            return result
                        # 6. Else we did not solve it, so backtrack and
                        #    remove the move from the solution path (self.moves)
                        self.moves.pop()
                return None

        # You have to implement these:

        def __init__(self):
            # Be sure to set self.startArgs and self.startState here
            pass

        def stateSatisfiesConstraints(self, state):
            # return True if the state satisfies the solution constraints so far
            raise NotImplementedError

        def isSolutionState(self, state):
            # return True if the state is a solution
            raise NotImplementedError

        def getLegalMoves(self, state):
            # return a list of the legal moves from this state (but not
            # taking the solution constraints into account)
            raise NotImplementedError

        def doMove(self, state, move):
            # return a new state that results from applying the given
            # move to the given state
            raise NotImplementedError

    ##############################################
    # Generic State Class
    # Cited from https://www.cs.cmu.edu/~112/notes/notes-recursion-part2.html#whatIsBacktracking
    ##############################################

    class State(object):
        def __eq__(self, other): return (other != None) and self.__dict__ == other.__dict__
        def __hash__(self): return hash(str(self.__dict__)) # hack but works even with lists
        def __repr__(self): return str(self.__dict__)

    ##############################################
    # My Solver and State
    ##############################################
    class mazeMaker(BacktrackingPuzzleSolver):
        def __init__(self, singlePieceLengths):
            self.singlePieceLengths = singlePieceLengths
            self.startState = mazeState([(margin, margin)], [])

        def stateSatisfiesConstraints(self, state):
            n = len(state.routePositions)
            (x0, y0) = state.routePositions[-1]
            # in the board
            if ((x0 < margin or x0 > displayW-margin) or
                (y0 < margin or y0 > displayH-margin)):
                return False 
            
            # not overlapping
            (x1, y1) = state.routePositions[-2]
            lst = state.routePositions[-n:-2]
            for (x2, y2) in lst:
                if x0 == x1 == x2:
                    if ((min(y1, y2) <= y0 <= max(y1, y2))): return False
                elif y0 == y1 == y2:
                    if ((min(x1, x2) <= x0 <= max(x1, x2))): return False
            
            for i in range(len(state.routePositions)-3): 
                start2, end2 = state.routePositions[i], state.routePositions[i+1]
                if lineSegmentIntersect((x0, y0), (x1, y1), start2, end2): return False
        
            # not going in the same direction above 5 times 
            if len(state.routeDirections) >= 5:
                lastSixMoves = state.routeDirections[-6:-1]
                if len(set(lastSixMoves)) == 1 : return False
            
            return True
            
        def isSolutionState(self, state):
            return (len(state.routePositions) == len(self.singlePieceLengths)+1)

        def getLegalMoves(self, state):
            availableDirections = defaultDirections
            random.shuffle(availableDirections)
            return availableDirections

        def doMove(self, state, move): # move is a tuple
            (lastX, lastY) = state.routePositions[-1]
            incrementLength = self.singlePieceLengths[len(state.routePositions)-1]
            (moveX, moveY) = (move[0]*incrementLength, move[1]*incrementLength)
            (newX, newY) = (lastX+moveX, lastY+moveY)
            newRoutePositions = copy.copy(state.routePositions)
            newRoutePositions.append((newX, newY))
            newRouteDirections = copy.copy(state.routeDirections)
            newRouteDirections.append(move)
            return mazeState(newRoutePositions, newRouteDirections)

    class mazeState(State):
        def __init__(self, routePositions, routeDirections):
            self.routePositions = routePositions
            self.routeDirections = routeDirections

        def checkBlankness(self):
            bounds = []
            xRange = [x for x in range(0, displayW, rectW)]
            yRange = [y for y in range(0, displayH, rectH)]
            random.shuffle(xRange)
            random.shuffle(yRange)
            
            for x in xRange:
                for y in yRange:
                    if not self.localPointIntersect(pygame.rect.Rect((x, y), (rectW, rectH))):
                        bounds.append((x, y))
            return None if bounds == [] else bounds

        def localPointIntersect(self, rect):
            for (nodeX, nodeY) in self.routePositions:
                if rect.collidepoint((nodeX, nodeY)):
                    return True
            return False # no point in that rectangular area
        
        @staticmethod
        def getEndPoint(lastPoint, secondLastPoint):
            (x, y) = lastPoint
            (lastx, lasty) = secondLastPoint
            endNode = None
            distances = None
            if lastx == x and lasty < y:
                distances = [displayH-y, displayW-x, x] 
            elif lastx == x and lasty > y:
                distances = [y, displayW-x, x]
            elif lasty == y and lastx < x:
                distances = [y, displayH-y, displayW-x]
            elif lasty == y and lastx > x:
                distances = [y, displayH-y, x]
            minDistance = min(distances)

            if minDistance == displayH-y: endNode = (x, displayH-margin)
            elif minDistance == y: endNode = (x, margin)
            elif minDistance == displayW-x: endNode = (displayW-margin, y)
            elif minDistance == x: endNode = (margin, y)
            return endNode
        
        def drawMaze(self, color):
            # drawBaics maze 
            endNode = mazeState.getEndPoint(self.routePositions[-1], self.routePositions[-2])
            newPositions = self.routePositions + [endNode]

            for i in range(len(newPositions)):
                (x0, y0) = (int(newPositions[i][0]), int(newPositions[i][1]))
                if ((i == 0) or (i == len(newPositions)-1)):
                    pygame.draw.circle(mainDisplay, color, (x0, y0), 5)
                else: pygame.draw.circle(mainDisplay, white, (x0, y0), 5)
                
                if i < len(newPositions)-1:
                    (x1, y1) = (int(newPositions[i+1][0]), int(newPositions[i+1][1]))
                    pygame.draw.line(mainDisplay, white, (x0, y0),
                                    (x1, y1), 2)
                pygame.display.update()

    class subMazeMaker(mazeMaker):
        def __init__(self, startState, bounds):
            self.startState = startState
            self.bounds = (bounds[0], bounds[1], bounds[0]+rectW, bounds[1]+rectH)
            self.defaultLength = rectW/3

        def pointGoBeyondBounds(self, state):
            (lastX, lastY) = state.routePositions[-1]
            return ((lastX < self.bounds[0]) or (lastX > self.bounds[2]) or 
                    (lastY < self.bounds[1]) or (lastY > self.bounds[3]))

        def stateSatisfiesConstraints(self, state):
            if len(state.routeDirections) >= 4:
                lastMoves = state.routeDirections[-4:0]
                if len(set(lastMoves)) == 1 : return False
            if self.pointGoBeyondBounds(state): return False
            if super().stateSatisfiesConstraints(state):
                return True
        
        def doMove(self, state, move):
            (lastX, lastY) = state.routePositions[-1]
            (newX, newY) = (lastX+self.defaultLength*move[0], lastY+self.defaultLength*move[1])
            newRoutePositions = state.routePositions + [(newX, newY)]
            newRouteDirections = state.routeDirections + [move]
            return mazeState(newRoutePositions, newRouteDirections)

        def isSolutionState(self, state):
            return len(self.moves) == 6

    def makeMaze(generator):
        button = Button('Play Maze', displayW/12, displayH/12, playMaze)

        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                button.get_pressed(event)

            mainDisplay.fill(black)
            textSurf, textRect = createText('Your Maze', brightYellow, 40)
            textRect.center = (displayW/2, displayH/8)

            for i in range(len(mazes)):
                    if i == 0:
                        mazes[i].drawMaze(red)
                    else:
                        mazes[i].drawMaze(white)

            button.draw()
            mainDisplay.blit(textSurf, textRect)
            pygame.display.update()

    def playMaze():

        def startPlayMaze():
            availableDirections = getAvailableDirections(solutionPath, 0)
            playFromMaze(solutionPath, 0, availableDirections)  
            
        def playFromMaze(path, startIndex, availableDirections, selectedNodes=None):
            startPos = path[startIndex]
            selectedIndex = startIndex
            selectedDirection = None
            success = False
            if selectedNodes == None:
                selectedNodes = [(margin, margin)]
                selectedIndex = 0
                
            done = False
            while not done:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        done = True
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_DOWN: 
                            selectedDirection = (0, +1)
                        elif event.key == pygame.K_UP: selectedDirection = (0, -1)
                        elif event.key == pygame.K_LEFT: selectedDirection = (-1, 0)
                        elif event.key == pygame.K_RIGHT: 
                            selectedDirection = (+1, 0)
        
                if selectedDirection != None:
                    (dx, dy) = selectedDirection
                    currentNode = path[selectedIndex]
                    nextNode = path[selectedIndex+1] if selectedIndex < len(path)-1 else None 
                    preNode = path[selectedIndex-1] if selectedIndex > 0 else None
                    
                    try:
                        if currentNode in startPoses:
                            if path == solutionPath:
                                newPath = branchPaths[startPoses.index(currentNode)] 
                            else:
                                newPath = solutionPath
                            startIndex = newPath.index(currentNode)
                            availableDirections = getAvailableDirections(newPath, startIndex)
                            if selectedDirection in availableDirections:
                                playFromMaze(newPath, startIndex, availableDirections, selectedNodes)
                            else: pass

                        if ((nextNode[0]-currentNode[0] > 0) == (dx > 0) and 
                            (nextNode[1]-currentNode[1] > 0) == (dy > 0)):
                            selectedNodes.append(nextNode)
                            selectedIndex += 1

                        elif ((currentNode[0]-preNode[0] > 0) == (dx < 0) and 
                            (currentNode[1]-preNode[1] > 0) == (dy < 0)):
                            selectedNodes.remove(currentNode)
                            selectedIndex -= 1
                    
                    except:
                        if preNode == path[-2]:
                            success = True
                        elif nextNode == None:
                            pass
                
                mainDisplay.fill(black)
                for i in range(len(mazes)):
                    if i == 0:
                        mazes[i].drawMaze(red)
                    else:
                        mazes[i].drawMaze(white)

                for i in range(len(selectedNodes)):
                    (x0, y0) = (int(selectedNodes[i][0]), int(selectedNodes[i][1]))
                    if i < len(selectedNodes)-1:
                        (x1, y1) = (int(selectedNodes[i+1][0]), int(selectedNodes[i+1][1]))
                        pygame.draw.line(mainDisplay, darkYellow, (x0, y0), (x1, y1), 2)
                    pygame.draw.circle(mainDisplay, green, (x0, y0), 5)

                if path == solutionPath and success:
                    drawSolutionPath(solutionPath)

                selectedDirection = None    
                pygame.display.update()

        def drawSolutionPath(solutionPath):
            button = Button('Main Menu', displayW/12, displayH/12, runApp)
            endNode = mazeState.getEndPoint(solutionPath[-1], solutionPath[-2])
            solutionPath += [endNode]
            done = False

            while not done:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        done = True
                    button.get_pressed(event)

                for i in range(len(solutionPath)):
                    (x0, y0) = (int(solutionPath[i][0]), int(solutionPath[i][1]))
                
                    if i < len(solutionPath)-1:
                        (x1, y1) = (int(solutionPath[i+1][0]), int(solutionPath[i+1][1]))
                        pygame.draw.line(mainDisplay, pink, (x0, y0), (x1, y1), 2)
                    pygame.draw.circle(mainDisplay, red, (x0, y0), 5)
                button.draw()
                
                pygame.display.update()
            
        selectedDirection = None
        solutionPath = maze.routePositions
        ends = [solutionPath[0], solutionPath[-1]]
        branchPaths = [maze.routePositions for maze in mazes[1:]]
        startPoses = [branchPath[0] for branchPath in branchPaths]

        startPlayMaze()
   
    singlePieceLengths = getSinglePieceLengths(tempPath)
    print("You get the singlePieceLengths")
    generator = mazeMaker(singlePieceLengths)
    print("And you get the maze generator")

    bounds, maze = findBestMaze(generator)
    print("you should be alright here!")
    n = len(bounds)
    startPosList = [getStartPos(maze.routePositions, bounds[i]) for i in range(n)]
    subGeneratorList = [subMazeMaker(mazeState(startPosList[i], []), bounds[i]) for i in range(n)]

    mazes = [maze]
    for subGenerator in subGeneratorList:
        submaze = findBestSubMaze(subGenerator)
        mazes.append(submaze)
    makeMaze(generator)

runApp()