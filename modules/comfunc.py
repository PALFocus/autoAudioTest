# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 10:54:34 2019

@author: daniel
"""
import os

# ICMP parameters

ICMP_ECHOREPLY  =    0 # Echo reply (per RFC792)
ICMP_ECHO       =    8 # Echo request (per RFC792)
ICMP_MAX_RECV   = 2048 # Max size of incoming buffer

MAX_SLEEP = 1000


"""
Functions
"""
def ask_yes_no(question):
    """
    Ask a yes or no questions.
    """
    response = None
    while response not in ('y', 'n'):
        response = input(question).lower()
    return response

def cal_difftime(start, end):
    time_span = end - start 
    
    elapse_time    = time_span.total_seconds()
    
    elapse_days    = int(elapse_time // (3600 * 24))
    elapse_hours   = int((elapse_time - elapse_days * 24 * 3600) // 3600)
    elapse_minutes = int((elapse_time - elapse_days * 24 * 3600 - elapse_hours * 3600) // 60)
    elapse_seconds = int(elapse_time % 60)
    
    str_elapse_time = "%d Days, %d Hours, %d Minutes, %d Seconds" \
                       %(elapse_days,elapse_hours,elapse_minutes,elapse_seconds)
    return str_elapse_time

def cal_estimate_time(estimate_time):    
    elapse_days    = int(estimate_time // (3600 * 24))
    elapse_hours   = int((estimate_time - elapse_days * 24 * 3600) // 3600)
    elapse_minutes = int((estimate_time - elapse_days * 24 * 3600 - elapse_hours * 3600) // 60)
    elapse_seconds = int(estimate_time % 60)
    
    str_elapse_time = "%d Days, %d Hours, %d Minutes, %d Seconds" \
                       %(elapse_days,elapse_hours,elapse_minutes,elapse_seconds)
    return str_elapse_time

def hex_show(buf, logfile):
    try:
        result = ''  
        hLen = len(buf)  
        for i in range(hLen):  
            hvol = buf[i]
            hhex = '%02x'%hvol  
            result += hhex+' '  
        print('hex show:%s'%result)
        print('hex show:%s'%result, file=logfile)
    except:
        pass
    
def IsValuePass(val, set, accuracy, tolarence):
    range = set * accuracy + tolarence
    if (val < set - range):
        
        return -1
    elif (val > set + range):
        return +1
    
    return 0

def checksum(source_string):
    """
    A port of the functionality of in_cksum() from ping.c
    Ideally this would act on the string as a series of 16-bit ints (host
    packed), but this works.
    Network data is big-endian, hosts are typically little-endian
    """
    countTo = (int(len(source_string)/2))*2
    sum = 0
    count = 0

    # Handle bytes in pairs (decoding as short ints)
    loByte = 0
    hiByte = 0
    while count < countTo:
        if (sys.byteorder == "little"):
            loByte = source_string[count]
            hiByte = source_string[count + 1]
        else:
            loByte = source_string[count + 1]
            hiByte = source_string[count]
        sum = sum + (hiByte * 256 + loByte)
        count += 2

    # Handle last byte if applicable (odd-number of bytes)
    # Endianness should be irrelevant in this case
    if countTo < len(source_string): # Check for odd length
        loByte = source_string[len(source_string)-1]
        sum += loByte

    sum &= 0xffffffff # Truncate sum to 32 bits (a variance from ping.c, which
                      # uses signed ints, but overflow is unlikely in ping)

    sum = (sum >> 16) + (sum & 0xffff)    # Add high 16 bits to low 16 bits
    sum += (sum >> 16)                    # Add carry from above (if any)
    answer = ~sum & 0xffff              # Invert and truncate to 16 bits
    answer = socket.htons(answer)

    return answer

def do_one_ex(destIP, timeout, mySeqNumber, numDataBytes, logFile):
    """
    Returns either the delay (in ms) or None on timeout.
    """
    global myStats

    delay = None

    try: # One could use UDP here, but it's obscure
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    except socket.error as e:
        print("failed. (socket error: '%s')" % e.args[1], file=logFile)
        raise # raise the original error

    my_ID = os.getpid() & 0xFFFF

    sentTime = send_one_ping(mySocket, destIP, my_ID, mySeqNumber, numDataBytes)
    if sentTime == None:
        mySocket.close()
        return delay

    myStats.pktsSent += 1;

    recvTime, dataSize, iphSrcIP, icmpSeqNumber, iphTTL = receive_one_ping(mySocket, my_ID, timeout)

    mySocket.close()

    if recvTime:
        delay = (recvTime-sentTime)*1000
        print("%d bytes from %s: icmp_seq=%d ttl=%d time=%d ms" % (
            dataSize, socket.inet_ntoa(struct.pack("!I", iphSrcIP)), icmpSeqNumber, iphTTL, delay)
        , file=logFile)
        myStats.pktsRcvd += 1;
        myStats.totTime += delay
        if myStats.minTime > delay:
            myStats.minTime = delay
        if myStats.maxTime < delay:
            myStats.maxTime = delay
    else:
        delay = None
        print("Request timed out.", file=logFile)

    return delay

def send_one_ping(mySocket, destIP, myID, mySeqNumber, numDataBytes):
    """
    Send one ping to the given >destIP<.
    """
    destIP  =  socket.gethostbyname(destIP)

    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0

    # Make a dummy heder with a 0 checksum.
    header = struct.pack(
        "!BBHHH", ICMP_ECHO, 0, myChecksum, myID, mySeqNumber
    )

    padBytes = []
    startVal = 0x42
    for i in range(startVal, startVal + (numDataBytes)):
        padBytes += [(i & 0xff)]  # Keep chars in the 0-255 range
    data = bytes(padBytes)

    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data) # Checksum is in network order

    # Now that we have the right checksum, we put that in. It's just easier
    # to make up a new header than to stuff it into the dummy.
    header = struct.pack(
        "!BBHHH", ICMP_ECHO, 0, myChecksum, myID, mySeqNumber
    )

    packet = header + data

    sendTime = time.time()

    try:
        mySocket.sendto(packet, (destIP, 1)) # Port number is irrelevant for ICMP
    except socket.error as e:
        print("General failure (%s)" % (e.args[1]))
        return

    return sendTime

def receive_one_ping(mySocket, myID, timeout):
    """
    Receive the ping from the socket. Timeout = in ms
    """
    timeLeft = timeout/1000

    while True: # Loop while waiting for packet or timeout
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return None, 0, 0, 0, 0

        timeReceived = time.time()

        recPacket, addr = mySocket.recvfrom(ICMP_MAX_RECV)

        ipHeader = recPacket[:20]
        iphVersion, iphTypeOfSvc, iphLength, \
        iphID, iphFlags, iphTTL, iphProtocol, \
        iphChecksum, iphSrcIP, iphDestIP = struct.unpack(
            "!BBHHHBBHII", ipHeader
        )

        icmpHeader = recPacket[20:28]
        icmpType, icmpCode, icmpChecksum, \
        icmpPacketID, icmpSeqNumber = struct.unpack(
            "!BBHHH", icmpHeader
        )

        if icmpPacketID == myID: # Our packet
            dataSize = len(recPacket) - 28
            return timeReceived, dataSize, iphSrcIP, icmpSeqNumber, iphTTL

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return None, 0, 0, 0, 0

def dump_stats_ex(logFile):
    """
    Show stats when pings are done
    """
    global myStats

    print("\n----%s PYTHON PING Statistics----" % (myStats.thisIP), file=logFile)

    if myStats.pktsSent > 0:
        myStats.fracLoss = (myStats.pktsSent - myStats.pktsRcvd)/myStats.pktsSent

    print("%d packets transmitted, %d packets received, %0.1f%% packet loss" % (
        myStats.pktsSent, myStats.pktsRcvd, 100.0 * myStats.fracLoss
    ), file=logFile)

    if myStats.pktsRcvd > 0:
        print("round-trip (ms)  min/avg/max = %d/%0.1f/%d" % (
            myStats.minTime, myStats.totTime/myStats.pktsRcvd, myStats.maxTime
        ), file=logFile)
        
    return

def signal_handler(signum, frame):
    """
    Handle exit via signals
    """
    dump_stats()
    print("\n(Terminated with signal %d)\n" % (signum))
    sys.exit(0)
    
def verbose_ping_ex(hostname, logFile, timeout = 1000, count = 5, numDataBytes = 55):
    """
    Send >count< ping to >destIP< with the given >timeout< and display
    the result.
    """
    global myStats

    signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl-C
    if hasattr(signal, "SIGBREAK"):
        # Handle Ctrl-Break e.g. under Windows
        signal.signal(signal.SIGBREAK, signal_handler)

    myStats = MyStats() # Reset the stats

    mySeqNumber = 0 # Starting value

    try:
        destIP = socket.gethostbyname(hostname)
        print("\nPYTHON PING %s (%s): %d data bytes" % (hostname, destIP, numDataBytes), file=logFile)
    except socket.gaierror as e:
        print("\nPYTHON PING: Unknown host: %s (%s)" % (hostname, e.args[1]), file=logFile)
        print()
        return

    myStats.thisIP = destIP

    for i in range(count):
        delay = do_one_ex(destIP, timeout, mySeqNumber, numDataBytes, logFile)

        if delay == None:
            delay = 0

        mySeqNumber += 1

        # Pause for the remainder of the MAX_SLEEP period (if applicable)
        if (MAX_SLEEP > delay):
            time.sleep((MAX_SLEEP - delay)/1000)

    dump_stats_ex(logFile)
