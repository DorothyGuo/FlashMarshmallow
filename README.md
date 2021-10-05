# FlashMarshmallow

## Project Description 
The name of my term project is called ‘Flash Marshmallow’. It is a music builder that allows the user to build a piece of music of their preferred music genre (or several genres) and get a board game designed based on the music they build back. 
## Competitive Analysis 
My project is related to music, a topic that many people choose for their projects, which means that the way we collect and analyze the music may overlap. However, my project has two points that are distinct. The first point is that users can build their own music by selecting music pieces themselves through my project. And the second point is that the music is visualized not by simply showing some patterns but by designing a board game. So although the theme of my project is music, it also has many extensions 
## Structural Plan 
My project has three main parts. The first part is the selection, modification, and analysis of the music. I store the songs of different genres in different folders in advance to access later. I also have a collection of functions that do the works like cutting songs into pieces, store the pieces, and put the pieces together. I will call these functions accordingly when needed in the main loop of my project. The second part is the interaction between the user and my project. The interface is mainly executed by pygame, including functions to create and connect different parts of the project. The third part is the generation of the board, which takes the music pieces selected by the user, analyze the song pieces, and create a board accordingly. 
## Algorithmic Plan 
The trickiest part of my project would be to concatenate the song pieces and use them to generate the board. To achieve this, I plan to select several features of the music and connect each of them to different features of the board. So I divide the analysis into different parts and distribute them to different functions. For example, the pitch of the music may be related to the color of the board. So I have a function that 
gets the pitch of the music, assign it to a specific color (or a series of colors) to create the board. 
## Timeline Plan 
I plan to finish the part to collect song pieces based on users’ actions and concatenate them (and modify) over the weekend. By TP2 I want to be able to generate a simple board 
based on the information I get from the music. And during Thanksgiving Day I want to improve on the features of the board, and the overall functionality of the interface. 
## Stage2 Update 
There are three changes from Stage1. 
1.	Besides the modules I mention in Stage proposal, I use librosa to extract music feature, sox to mix music. 
2.	Instead of focussing on modify or visualize the music, I decide to focus more on using music to generate a maze and allow users to play the maze game 
3.	To generate the maze, I take each beat as a node and the length between two nodes is decided by the time between two beats. After I use the music to generate a solution path of the maze (by backtracking), I complete the design of the maze by randomly choosing some nodes on solution path and draw branches from them. And I will also make the maze actually playable. 
## Final Update
The progression after Stage2 basically just followed the ideas listed in Stage2 update. There’s only one slight difference. Instead of randomly choosing nodes on solution path to draw the branches, I check whether there’s black area after the solution path is drawn. I find the blank area, fill it up by finding the nearest point to that area on the solution path and doing the backtracking again limited to that are. When the user is actually playing the maze, I use recursion to achieve the transitions between different submazes. 
