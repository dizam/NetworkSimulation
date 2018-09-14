import random
import math
import sys
import Queue
import heapq

class Arrival:
	def __init__(self, aTime):
		self.time = aTime
	def getTime(self):
		return self.time
	def __cmp__(self, other): 
		#for use in heap
		return cmp(self.time, other.time)

class Departure:
	def __init__(self, dTime):
		self.time = dTime
	def getTime(self):
		return self.time
	def __cmp__(self, other): 
		#for use in heap
		return cmp(self.time, other.time)

def negative_EXP(rate):
	u = random.random();
	return ((-1/rate) * math.log(1 - u))

if __name__ == '__main__':
	if len(sys.argv) > 1: #if there are arguments
		MAXBUFFER = int(sys.argv[1]) #set max buffer size for queue in arg
		aRate = float(sys.argv[2]) #set arrival rate lambda in arg
	else:
		print "Usage: packet.py [MAXBUFFERSIZE] [LAMBDA]" #no arguments, just exit
		sys.exit(0)

	tRate = 1
	busy = 0
	MQL = 0
	dropped = 0
	length = 0
	time = 0
	buffer = Queue.Queue(MAXBUFFER) #make queue for packets
	GEL = [] #initialization
	a1 = Arrival(time + negative_EXP(aRate)) #first arrival event
	heapq.heappush(GEL, a1) #put first arrival into heap

	for i in range(0, 100000):
		currentEvent = heapq.heappop(GEL)
		if isinstance(currentEvent, Arrival):
			if length >= 1:
				busy += currentEvent.getTime() - time 
				#server is busy when something is in queue (stat)
				MQL += length * (currentEvent.getTime() - time) 
				#MQL = sum of area of rectangles between each event (stat)
			time = currentEvent.getTime() #update time
			anext = Arrival(time + negative_EXP(aRate)) #make next arrival event
			heapq.heappush(GEL, anext) #put next arrival event into GEL
			if length == 0:
				length += 1 #increment queue length
				dnext = Departure(time + negative_EXP(tRate)) 
				#make departure event for this packet
				heapq.heappush(GEL, dnext) #put departure event into GEL
			else:
				if (length - 1) < MAXBUFFER:
					buffer.put(anext) #put packet into queue
					length += 1 #increment queue length
				else:
					dropped += 1 #dropped packet
		else: 
			busy += (currentEvent.getTime() - time) #utilization statistic
			MQL += length * (currentEvent.getTime() - time) #MQL statistic
			time = currentEvent.getTime() #update time
			length -= 1 #decrement queue length for a departure
			if (length > 0):
				packet = buffer.get() #dequeue the first packet from the buffer
				dnext = Departure(time + negative_EXP(tRate)) 
				#make departure event for packet from buffer
				heapq.heappush(GEL, dnext) #put departure event into GEL

	util = busy/time
	mean = MQL/time
	print "Utilization: ", util
	print "Mean Queue Length: ", mean
	print "Packets dropped: ", dropped



