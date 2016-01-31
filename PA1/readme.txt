a. A brief description

The python files Server.py and Client.py realise simple chat functions. Server.py acts as a server and can be connected to multiple Client.py using TCP connections. With Server.py running, users can run Client.py to login to the chatroom, send broadcast or private messages to each other, and perform other commands as well.  Different users are handled in the server as different threads, and information for each user is handled (read and written) through sockets. 

Client.py takes two parameters with it, which is the IP address and port number it will connect to. If the given IP address is valid, a socket will be created for the user and connect to server (and if otherwise an error message will pop out). Then select.select function will determine the socket behaviour (read, write, etc.). If the program was interrupted by the user by control+C, the program will exit and pop a message. 

Server.py takes one input, which is the port number the server is listening at. The server create a socket first, and then creates a new thread for each new user. The server log in the user if correct username and password combination is provided. If the login information is not correct, the user will not be able to send commands and might be blocked for a while. After successfully logged in, the user will be able to run many commands such as check wholes is online. Those actions were performed by functions in Server.py. Invalid commands will trigger an error message.

This project also contains a txt file user_pass.txt. It records all the valid username and password combination in the manner of 

<username> <password>

Ex:	columbia 116bway


b. Details on development environment

This simple chat room was developed in a MAC os with Python 2.7.10. This may not work in Windows.


c. Running Instruction

To run the server program, the user should start a terminal and type:

python Server.py <port_number>

Ex:	python Server.py 4119

The client program should be run by type the following in terminal:

python Client.py <IP_address> <port_number>

Ex:	python Client.py 1.2.3.4 4119

If successful, The user will be asked to input username in the client’s terminal. The username used should be one of the recorded username in user_pass.txt. If input correctly, user will be asked to input password. The password should also be in user_pass.txt and corresponds to the username provided. Otherwise an error message will pop out and after several (determined by the variable LOGIN_TIMES in Server.py) tries, the user will be blocked for a while (determined by the variable BLOCK_TIME in Server.py).

If the password meets the requirement, the client will be logged in and a welcome message will pop up on the client’s terminal. Then the client can input different commands, as suggested in part d of this file. Notice that if the client does not run any command for too long time, the server will time out this user and log the user out. The time out time is determined by the variable TIME_OUT in Server.py.


d. Sample commands

The commands that can be run by the client’s are as listed:

whoeles

wholast <number> (number should be between 0 and 60)

broadcast message <message>

broadcast user <user> <user> … <user> message <message>

message <user> <message>

personalintro

Ex1:	Username:csee4119

	Password:lotsofassignments
	Login successful, Welcome to simple chat server!
	Command:whoelse
	The currently online users are:
	(Not found)

	Command:personalintro
	Please enter your personal introduction:
	The best course ever

	Command:logout

	Logging off
	Disconnected

Ex2:	Username:columbia

	Password:116bway
	Login successful, Welcome to simple chat server!

	Command:message seas hello
	(Receiver seas is currently offline, message will be delivered when they log in next time)

	Command:wholast 10
	The users that are online in the last 10 minutes are:
	facebook   <An website>
	csee4119   <The best course ever>

Ex3:	Username:seas

	Password:summerisover
	Login successful, Welcome to simple chat server!
	Your offline messages:
	columbia: hello <private message>


e. Additional functions

Apart from the requested functions, I added an offline message function. When a message was sent (no matter if it is broadcast, partially broadcast or private) and the user is not online, the system will notify the sender and present the message to the receiver next time he/she logged in as a offline message, as the example shown in part d. The process is as follow:

Sender:    Command:message seas hello
           (Receiver seas is currently offline, message will be delivered when they log in next time)
Receiver:  Login successful, Welcome to simple chat server!
	    Your offline messages:
	    columbia: hello <private message>

I also included a new function called personalintro, by running this function, the server will ask for an input, and clients will input their personal introductions; when other user run “whoelse” or “wholast” command next time, they will be able to see both the username and personal introduction(if set). The process is as follow: 

One user:	Command:personalintro
		Please enter your personal introduction:
		The best course ever
Other user:	Command:whoelse
		The currently online users are:
		csee4119   <The best course ever>




