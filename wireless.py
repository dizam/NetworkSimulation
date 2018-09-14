import heapq
import sys
import math
import random
import Queue

SIMULATION_TIME = 1000
aRate = 0.3
N = 10
DIFS = 0.1
SIFS = 0.05
TIMEOUT = 5
busyTime = 0
busy = False
bytes_sent = 0
totalDelay = 0
INFINITEBUFFERSIZE = 40000000
pulled1 = False
pulled2 = False
pulled3 = False

class Host:
	def __init__(self, hostNum):
		self.hostNum = hostNum
		self.waiting = False
		self.fails = 0
		self.timeoutStart = 0
		self.heldPacket = None
		self.backoff = 0
		self.delay = 0
		self.queue = Queue.Queue(INFINITEBUFFERSIZE) #make queue for packets

class UserToHost:
	def __init__(self, uTime, sourceHost, destHost):
		self.time = uTime
		self.sourceHost = sourceHost
		self.destHost = destHost
	def getTime(self):
		return self.time
	def __cmp__(self, other):
		return cmp(self.time, other.time)

class SendData:
	def __init__(self, pTime, sourceHost, destHost, packetSize, startTime):
		self.time = pTime
		self.sourceHost = sourceHost
		self.destHost = destHost
		self.packetSize = packetSize
		self.startTime = startTime
		self.queueDelay = 0
	def getTime(self):
		return self.time
	def __cmp__(self, other):
		return cmp(self.time, other.time)

class SendACK:
	def __init__(self, aTime, sourceHost, destHost, packetSize, startTime):
		self.time = aTime
		self.sourceHost = sourceHost
		self.destHost = destHost
		self.packetSize = packetSize
		self.startTime = startTime
		self.queueDelay = 0
	def getTime(self):
		return self.time
	def __cmp__(self, other):
		return cmp(self.time, other.time)

def getTransTime(size):  # returns transmission time of message
    return float(1000 * (size * 8)) / float((11 * 1000000))


def negative_EXP(rate):  # generation of arrivals
    u = random.random()
    return ((-1 / rate) * math.log(1 - u))


def negative_EXP_size(rate):  # returns size of message
    u = negative_EXP(rate) * 2800
    while (u <= 0 or u > 1544):
    	u = (int) (negative_EXP(rate) * 2800)
    return (int)(u)

def processEvent(busy, idleTime, EventPass):
	if (EventPass is not None):
		Event = EventPass
	else:
		Event = heapq.heappop(GEL)
	if isinstance(Event, UserToHost):
		processUserToHost(Event.time, Event.sourceHost, Event.destHost, idleTime, busy)
	elif isinstance(Event, SendData):
		processSendData(Event.time, Event.sourceHost, Event.destHost, Event.packetSize, busy, idleTime)
	elif isinstance(Event, SendACK):
		processSendACK(Event.time, Event.sourceHost, Event.destHost, Event.packetSize, busy, idleTime)

def processUserToHost(nTime, source, dest, idleTime, busy):
	global totalDelay
	global busyTime
	global pulled1
	a1 = UserToHost(nTime + negative_EXP(aRate), source, dest)
	heapq.heappush(GEL, a1)
	packetSize = negative_EXP_size(aRate)
	sendTime = getTransTime(packetSize)
	packet = SendData(nTime + DIFS + sendTime, source, dest, packetSize, nTime)
	time = nTime
	if (hosts[source].waiting):
		if (nTime - hosts[source].timeoutStart >= TIMEOUT):
			packet = hosts[source].heldPacket
			hosts[source].fails += 1
			hosts[source].backoff = getBackoffTime(hosts[source].fails)
			totalDelay+=hosts[source].backoff
			hosts[source].delay += hosts[source].backoff
			hosts[dest].queue.put(packet)
			heapq.heappush(GEL, packet)
	if (busy):
		hosts[source].fails+=1
		hosts[source].backoff = getBackoffTime(hosts[source].fails)
		totalDelay+=hosts[source].backoff
		hosts[source].delay += hosts[source].backoff
		hosts[source].heldPacket = packet
	if (not busy and not hosts[source].waiting and hosts[source].backoff <= 0):
		busyTime = sendTime
		hosts[source].waiting = True
		hosts[source].fails = 0
		hosts[source].timeoutStart = time
		hosts[source].heldPacket = packet
		hosts[source].delay += sendTime
		totalDelay += sendTime
		hosts[dest].queue.put(packet)
		heapq.heappush(GEL, packet)
	if (hosts[source].backoff > 0 and not busy):
		hosts[source].backoff-=idleTime
		if (hosts[source].backoff <= 0 and hosts[source].fails <= 3):
			busyTime = sendTime
			hosts[source].waiting = True
			hosts[source].timeoutStart = time
			hosts[dest].queue.put(packet)
			heapq.heappush(GEL, packet)
			hosts[source].delay = 0
		elif (hosts[source].fails > 3):
			totalDelay-= (hosts[source].delay)
			hosts[source].delay=0

def processSendData(nTime, source, dest, packetSize, busy, idleTime):
	global pulled2
	global totalDelay
	if (hosts[dest].queue.qsize() != 0 and not pulled2):
		packet = hosts[dest].queue.get()
		qDelay = nTime - packet.startTime
		if (qDelay > 0):
			packet.queueDelay += (nTime - packet.startTime)
	#	print(packet.queueDelay)	
		pulled2 = True
		processEvent(busy, idleTime, packet)
		return
	else:
		pulled2 = False
	time = nTime
	busyTime = getTransTime(64)
	ACK = SendACK(nTime + SIFS + busyTime, source, dest, packetSize, nTime)
	hosts[dest].queue.put(ACK)
	heapq.heappush(GEL, ACK)

def processSendACK(nTime, source, dest, packetSize, busy, idleTime):
	global pulled3
	global totalDelay
	if (hosts[source].queue.qsize() != 0 and not pulled3):
		packet = hosts[source].queue.get()
		qDelay = nTime - packet.startTime
		if (qDelay > 0):
			packet.queueDelay += (nTime - packet.startTime)
		#if isinstance(packet, SendACK):
		totalDelay+=packet.queueDelay
		pulled3 = True
		processEvent(busy, idleTime, packet)
		return
	else:
		pulled3 = False
		hosts[source].waiting = False
		hosts[source].heldPacket = None
		hosts[source].fails = 0
		hosts[source].timeoutStart = 0
		hosts[source].backoff = 0
	global bytes_sent
	bytes_sent += packetSize


def getBackoffTime(fails):  # generation of backoff time
    u = random.random()
    return (int)(u * TIMEOUT) * (fails)

if __name__ == '__main__':
        busy = False 
        busyTime = 0
        bytes_sent = 0
        time = 0
        totalDelay = 0
        GEL = []
        hosts = []
        idleTime = 0

        for j in range(0, N):
        	hosts.append(Host(j))

        for j in range(0, N):
        	d = random.randint(0, N - 1)
        	while d == j:
        		d = random.randint(0, N - 1)

        	a1 = UserToHost(time + negative_EXP(aRate), j, d)
        	heapq.heappush(GEL, a1)  # put first arrival into heap

        while time < SIMULATION_TIME:
        	while (time < GEL[0].getTime()):
        		time += 0.01
        		if (not busy):
        			idleTime += 0.01
        		if (busyTime > 0):
        			#print(busyTime)
        			busy = True
        			busyTime -= 0.01
        		if (busyTime <= 0):
         			busy = False
         	processEvent(busy, idleTime, None)
         	idleTime = 0
        print("Lambda: ", aRate)
        print("Throughput: ", (bytes_sent/SIMULATION_TIME))
        #print("Total delay: ", totalDelay)
        print("Average network delay: " ,(totalDelay/(bytes_sent/SIMULATION_TIME)))
        #print("Average network delay: " ,(totalDelay/bytes_sent))


