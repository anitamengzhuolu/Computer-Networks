a. A brief description

The python file bfclient.py serves as the executable files of distributed client processes. Running a file means adding a client to the network. Clients will compute their distances to each other using Bellman-Ford algorithms with poisoned reversed, and users can check their routing tables and change the layout of the network by typing commands. Clients will send message to exchange there routing tables on a regular basis, and will respond to the termination of other client processes. 

b. Details on development environment

This simple chat room was developed in a MAC os with Python 2.6.9. This may not work in Windows.

c. Program features

User can use following commands to operate client:

SHOWRT: Shows the current routing table
LINKDOWN: block a current edge, and change the original weight to infinity
LINKUP: Resume an edge killed by LINKDOWN
CLOSE: Close a client and kill all the edges connecting to it, same effect can be achieve by CONTROL+C
BUILDEDGE (extra function): Build an edge connecting two clients in the network which are not neighbour to each other. Weights should be given.
NEIGHBOUR (extra function): Shows the current neighbour of this client.

d. Usage scenarios

To run the program, user should start a terminal window and cd to the target folder. Then in one terminal type (with IP addresses changed according to environment):

python bfclient.py 4115 3 192.168.0.4 4116 5


On other terminals type:

python bfclient.py 4116 3 192.168.0.4 4115 5 192.168.0.4 4118 5
python bfclient.py 4118 3 192.168.0.4 4116 5 192.168.0.4 4115 30
python bfclient.py 4117 3 192.168.0.4 4116 10

It will soon converge, now type command “SHOWRT” in the first terminal, we got:

SHOWRT
2015-12-16 22:25:25 Distance vector list is:
Destination = 192.168.0.4 4117, Cost = 15.0, Link = (192.168.0.4 4116)
Destination = 192.168.0.4 4116, Cost = 5.0, Link = (192.168.0.4 4116)
Destination = 192.168.0.4 4118, Cost = 10.0, Link = (192.168.0.4 4116)

Which shows us the routing table of the current client. By typing command “NEIGHBOR” we can see its current neighbour, like this:

NEIGHBOR
192.168.0.4 4116(5.0)
192.168.0.4 4118(30.0)

We will now break a link by typing command “LINKDOWN 192.168.0.4 4116”, after a while (which should be very quick) we can check its routing table again by typing “SHOWRT”, and we will get:

SHOWRT
2015-12-16 22:31:21 Distance vector list is:
Destination = 192.168.0.4 4117, Cost = 45.0, Link = (192.168.0.4 4116)
Destination = 192.168.0.4 4116, Cost = 35.0, Link = (192.168.0.4 4116)
Destination = 192.168.0.4 4118, Cost = 30.0, Link = (192.168.0.4 4118)

We then resume this link by typing command “LINKUP 192.168.0.4 4116”, and then we check its routing table again (“SHOWRT”), and get:

SHOWRT
2015-12-16 22:34:04 Distance vector list is:
Destination = 192.168.0.4 4117, Cost = 15.0, Link = (192.168.0.4 4116)
Destination = 192.168.0.4 4116, Cost = 5.0, Link = (192.168.0.4 4116)
Destination = 192.168.0.4 4118, Cost = 10.0, Link = (192.168.0.4 4116)

Now we a client (192.168.0.4 4116) decides to leave the system. User can type command “CLOSE” or press CONTROL+C. After some time (9s in this case), the map should be updated, so we perform “SHOWRT” on 4115’s terminal again and get:

SHOWRT
2015-12-16 22:40:15 Distance vector list is:
Destination = 192.168.0.4 4117, Cost = inf, Link = (192.168.0.4 4116)
Destination = 192.168.0.4 4116, Cost = inf, Link = (192.168.0.4 4116)
Destination = 192.168.0.4 4118, Cost = 30.0, Link = (192.168.0.4 4118)

We can see that 4115 can no longer reach 4117 and 4116 because of the disappearance of 4116, it can only reach 4118 now.

But we can add an edge from 4115 to 4117 (this is an extra function), by typing command “BUILDEDGE 192.168.0.4 4117 10”, in which 10 is the weight of the new path. We now check 4115’s routing table and it shows:

SHOWRT
2015-12-16 22:42:52 Distance vector list is:
Destination = 192.168.0.4 4117, Cost = 10.0, Link = (192.168.0.4 4117)
Destination = 192.168.0.4 4116, Cost = inf, Link = (192.168.0.4 4116)
Destination = 192.168.0.4 4118, Cost = 30.0, Link = (192.168.0.4 4118)

e. Protocol specification

Apart from implementing Bellman-Ford algorithm, this program also applied poisoned reverse. The updating message between clients are python dictionaries encapsulated in json, and transmitted by an UDP socket. In the message there are 3 information: sender name (with key “sender”), type of message (with key “type”) and contents. In update messages, contents are routing tables, and in build edge messages, contents are weights of the new edge. While in linkup and linkdown messages there are no content. 

f. Additional functions

(1) “NEIGHBOUR” command: by typing “NEIGHBOR” to command line user is able to view the client’s current neighbours. 
(2) “BUILDEDGE” command: by typing “BUILDEDGE”, a target client and the weight of the new edge, user can create an new edge between two existing nodes in the network. 
(3) Poisoned reverse: in the routing algorithm poisoned reverse is applied to improve efficiency.
