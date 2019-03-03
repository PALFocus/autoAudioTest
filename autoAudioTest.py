# -*- coding: utf-8 -*-
"""
This is a python learn test.
It's Interesting to use python to solve kind of integration auto test.
Created on Fri Jan 18 14:50:39 2019

@author: daniel
"""
import logging
import configparser
import datetime
import socket
import select
import time
import os
import serial
import binascii
import struct
import ctypes
import random
import getopt
import sys
import optparse
import signal


from mutagen.mp3 import MP3
from pygame import mixer

from modules.comfunc import *

INDEX_OF_SOURCE_METER_TOTAL_POWER = 23

LEN_OF_METER_SN                   = 12
METER_CMD_PREFIX                  = b'\x2F\x3F'
METER_CMD_SURFIX                  = b'\x21\x0D\x0A'

DEFAULT_INI_FILE_NAME             = 'steps.ini'
DEFAULT_TEST_PATH                 = 'tests'
DEFAULT_TEST_NAME                 = 'sample_tmjl'

"""
Rsp structre macros
"""
LEN_OF_RSP_AT                     = 1
LEN_OF_RSP_MODEL                  = 2
LEN_OF_RSP_STAR                   = 1

LEN_OF_RSP_KWH                    = 8
LEN_OF_RSP_VOLTAGE                = 4
LEN_OF_RSP_CURRENT                = 5
LEN_OF_RSP_POWER                  = 7
LEN_OF_RSP_COS                    = 4

LEN_OF_RSP_MAX_DMD                = 8
LEN_OF_RSP_TIME                   = 14
LEN_OF_RSP_CT                     = 4
LEN_OF_RSP_PULSE_COUNT            = 8
LEN_OF_RSP_PULSE_RATIO            = 4
LEN_OF_RSP_PULSE_HL               = 3
LEN_OF_RSP_RESERVE                = 20
LEN_OF_RSP_END                    = 4
LEN_OF_RSP_CRC                    = 2

"""
Global Configurations
"""
SECTION_OF_CONFIGURATION          = 'CONFIG'

VALUE_OF_SOFTWARE_SIMULATION      = 'SoftwareSimulation'
VALUE_OF_TEST_LOOPS               = 'NumOfTestLoops'
VALUE_OF_TEST_STEPS               = 'NumOfTestSteps'
VALUE_OF_TEST_INTERVAL            = 'IntervalOfTestSteps'
VALUE_OF_TEST_POWER_ACCURACY      = 'PowerAccuracy'
VALUE_OF_TEST_POWER_TOLERANCE     = 'PowerTolerance'
VALUE_OF_TEST_LOG_FILE            = 'LogFile'
VALUE_OF_PLAYER_INTERNAL          = 'PlayerInternal'
VALUE_OF_PLAYER_PATH              = 'PlayerPath'
VALUE_OF_PLAYER_NAME              = 'PlayerName'
VALUE_OF_PLAYER_OPTION            = 'PlayerOption'
VALUE_OF_SERIAL_PORT              = 'SerialPort'
VALUE_OF_METER_SN                 = 'MeterSN'
VALUE_OF_PING_ADDRESS             = 'PingAddress'

"""
Test Step Configurations
"""
SECTION_OF_TEST_STEPS_PREFIX      = 'STEP_'

VALUE_OF_OPERATION_NAME           = 'OpName'
VALUE_OF_AUDIO_NAME               = 'AudioName'
VALUE_OF_AUDIO_DURATION           = 'AudioDuration'
VALUE_OF_AUDIO_REAL_DURATION      = 'AudioRealDuration'
VALUE_OF_LIGHT_DELAY              = 'LightDelay'
VALUE_OF_LIGHT_POWER              = 'LightPower'

"""
Class
"""
class MyStats:
    thisIP   = "0.0.0.0"
    pktsSent = 0
    pktsRcvd = 0
    minTime  = 999999999
    maxTime  = 0
    totTime  = 0
    fracLoss = 1.0
    
class TestRecord:
    def __init__(self, step, result, set_, get):
        self.__rec = {'step': step, 'result': result, 'set': set_, 'getg': get}
    def record_set(self, step, result, set_, get):
        self.__rec = {'step': step, 'result': result, 'set': set_, 'getg': get}
    def step_get(self):
        return self.__rec['step']
    def result_get(self):
        return self.__rec['result']
    def preSet_get(self):
        return self.__rec['set']
    def testGet_get(self):
        return self.__rec['get']
    
class TestResult:
    def __init__(self):
        self.__res = {}
        self.__rec_total = 0
        self.__rec_passed_total = 0
        self.__rec_failed_total = 0
        self.__test_loops       = 0
        self.__test_steps       = 0
    def loops_set(self,loops):
        self.__test_loops       = loops
    def steps_set(self,steps):
        self.__test_steps       = steps
    def loops_get(self):
        return self.__test_loops
    def steps_get(self):
        return self.__test_steps
    def result_add(self, name, result, record):
        self.__res[name] = record
        self.__rec_total = self.__rec_total + 1
        if (result == True):
            self.__rec_passed_total = self.__rec_passed_total + 1
        else:
            self.__rec_failed_total = self.__rec_failed_total + 1
    def failed_get(self):
        return self.__rec_failed_total
    def passed_get(self):
        return self.__rec_passed_total
    def summary(self, logFile):
        print("=======================================")
        print("=======================================", file=logFile)
        
        if self.__test_loops:
            print("Summary:  loops %d"%self.__test_loops)
            print("Summary:  loops %d"%self.__test_loops, file=logFile)
        
        if self.__test_steps:
            print("Summary:  steps %d"%self.__test_steps)
            print("Summary:  steps %d"%self.__test_steps, file=logFile)

        if (self.__rec_failed_total + self.__rec_passed_total != self.__rec_total):
            print("Summary: attention, test record mis-matched.")
            print("Summary: attention, test record mis-matched.", file=logFile)
            
        print("---------------------------------------")
        print("---------------------------------------", file=logFile)
        print("Summary:  total %d steps tested."%self.__rec_total)
        print("Summary: passed %d steps"%self.__rec_passed_total)
        print("Summary: failed %d steps"%self.__rec_failed_total)
        
        print("Summary:  total %d steps tested."%self.__rec_total, file=logFile)
        print("Summary: passed %d steps"%self.__rec_passed_total, file=logFile)
        print("Summary: failed %d steps"%self.__rec_failed_total, file=logFile)

"""
Functions
"""
def port_open(ser, port):
    ser.port = port
    ser.baudrate = 9600
    ser.bytesize = 7
    ser.stopbits = 1
    ser.parity = "E"
    ser.open()
    return ser.isOpen()
 
def port_close(ser):
    ser.close()
    return(~ser.isOpen())
 
def send(send_data):
    if (ser.isOpen()):
        ser.write(send_data)
        #ser.write(send_data.encode('utf-8'))  #utf-8 编码发送
        #ser.write(binascii.a2b_hex(send_data))  #Hex发送
        #print("send succeed:",send_data)
        return True
    else:
        #print("send failed!")
        return False
        

def usage():
    print("autoAudioTest usage: e.g. autoAudioTest.exe -t sample_tmjl")
    print("            options:")
    print("                 -c: test configuration file, default:%s"%DEFAULT_INI_FILE_NAME)
    print("                 -p: path of test's files, default:%s"%DEFAULT_TEST_PATH)
    print("                 -t: test name, default:%s, which is an example of simulation"%DEFAULT_TEST_NAME)
    print("                 -h: manual of the tool")

"""
Main Entry
"""
opts, args = getopt.getopt(sys.argv[1:], "hc:p:t:")

tstPath = DEFAULT_TEST_PATH
tstName = DEFAULT_TEST_NAME
iniFile = DEFAULT_INI_FILE_NAME

for op, value in opts:
    if op == "-c":
        iniFile = value
    elif op == "-p":
        tstPath = value
    elif op == "-t":
        tstName = value
    elif op == "-h":
        usage()
        sys.exit(0)
        
if sys.platform == "win32":
    # On Windows, the best timer is time.clock()
    default_timer = time.clock
else:
    # On most other platforms the best timer is time.time()
    default_timer = time.time

myStats   = MyStats
workPath  = os.getcwd()
filePath  = "%s\%s\%s"%(tstPath, tstName, iniFile)
audioPath = "%s\%s"%(tstPath, tstName)

"""
Read Configurations
"""
cfgFile = configparser.RawConfigParser()
cfgFile.read(filePath)

SoftwareSimulation  = 1
numOfTestLoops      = 0
numOfTestSteps      = 0
intervalOfTestSteps = 0
powerAccuracy       = 0
powerTolerance      = 0

softwareSimulation  = int(cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_SOFTWARE_SIMULATION))
numOfTestLoops      = int(cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_TEST_LOOPS))
numOfTestSteps      = int(cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_TEST_STEPS))
intervalOfTestSteps = int(cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_TEST_INTERVAL))
powerAccuracy       = float(cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_TEST_POWER_ACCURACY))
powerTolerance      = float(cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_TEST_POWER_TOLERANCE))
logFile             = cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_TEST_LOG_FILE)
blPlayerInternal    = cfgFile.getboolean(SECTION_OF_CONFIGURATION, VALUE_OF_PLAYER_INTERNAL)
sPlayerPath         = cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_PLAYER_PATH)
sPlayerName         = cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_PLAYER_NAME)
sPlayerOption       = cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_PLAYER_OPTION)
serialPort          = cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_SERIAL_PORT)
meterSn             = cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_METER_SN)
pingAddress         = cfgFile.get(SECTION_OF_CONFIGURATION, VALUE_OF_PING_ADDRESS)

logPath =  "%s\%s\%s\%s"%(workPath, tstPath, tstName, logFile)
logfile = open(logPath, 'w')

trt = TestResult()

start_time       = datetime.datetime.now()
str_start_time   = start_time.strftime('%Y-%m-%d %H:%M:%S')

print("          Test Time: %s"%str_start_time)
print("          Test Time: %s"%str_start_time, file=logfile)

print(" softwareSimulation: %d"%softwareSimulation)
print(" softwareSimulation: %d"%softwareSimulation, file=logfile)

print("     numOfTestLoops: %d"%numOfTestLoops)
print("     numOfTestLoops: %d"%numOfTestLoops, file=logfile)
trt.loops_set(numOfTestLoops)

print("     numOfTestSteps: %d"%numOfTestSteps)
print("     numOfTestSteps: %d"%numOfTestSteps, file=logfile)
trt.steps_set(numOfTestSteps)

print("intervalOfTestSteps: %d seconds"%intervalOfTestSteps)
print("intervalOfTestSteps: %d seconds"%intervalOfTestSteps, file=logfile)

print("      powerAccuracy: %f"%powerAccuracy)
print("      powerAccuracy: %f"%powerAccuracy, file=logfile)

print("     powerTolerance: %f"%powerTolerance)
print("     powerTolerance: %f"%powerTolerance, file=logfile)

print("            logFile: %s"%logFile)
print("            logFile: %s"%logFile, file=logfile)

print("     PlayerInternal:", blPlayerInternal)
print("     PlayerInternal:", blPlayerInternal, file=logfile)

print("         PlayerPath:", sPlayerPath)
print("         PlayerPath:", sPlayerPath, file=logfile)

print("         PlayerName:", sPlayerName)
print("         PlayerName:", sPlayerName, file=logfile)

print("       PlayerOption:", sPlayerOption)
print("       PlayerOption:", sPlayerOption, file=logfile)

print("         SerialPort:", serialPort)
print("         SerialPort:", serialPort, file=logfile)

print("          Meter S/N:", meterSn)
print("          Meter S/N:", meterSn, file=logfile)

print("       Ping Address:", pingAddress)
print("       Ping Address:", pingAddress, file=logfile)

print("            cfgFile:", filePath)
print("            cfgFile:", filePath, file=logfile)

print("Current Working Directory:", os.getcwd())
print("Current Working Directory:", os.getcwd(), file=logfile)

print("=======================================")
print("=======================================", file=logfile)

i = 1
testSteps = {}
while i <= numOfTestSteps:
    key = SECTION_OF_TEST_STEPS_PREFIX + '%02d' % i
    
    print("Reading [%s]..."%key)
    opName        = cfgFile.get(key, VALUE_OF_OPERATION_NAME)
    audioName     = cfgFile.get(key, VALUE_OF_AUDIO_NAME)
    audioDuration = int(cfgFile.get(key, VALUE_OF_AUDIO_DURATION))
    lightDelay    = int(cfgFile.get(key, VALUE_OF_LIGHT_DELAY))
    lightPower    = float(cfgFile.get(key, VALUE_OF_LIGHT_POWER))
    
    print("Operation: %s"%opName)
    print("Operation: %s"%opName, file=logfile)
    
    print("    Audio: %s"%audioName)
    print("    Audio: %s"%audioName, file=logfile)
        
    if (0 == audioDuration):
        audioMp3 = MP3("%s\%s"%(audioPath, audioName))
        audioRealDuration = int(audioMp3.info.length + 1)
    else:
        audioRealDuration = 0

    print(" Duration: %d seconds (configured)"%audioDuration)
    print(" Duration: %d seconds (configured)"%audioDuration, file=logfile)

    print(" Duration: %d seconds (mp3 read from file)"%audioRealDuration)
    print(" Duration: %d seconds (mp3 read from file)"%audioRealDuration, file=logfile)

    print("    Delay: %d seconds"%lightDelay)
    print("    Delay: %d seconds"%lightDelay, file=logfile)
    
    print("    Power: %f"%lightPower)
    print("    Power: %f"%lightPower, file=logfile)
    
    print("---------------------------------------")
    print("---------------------------------------", file=logfile)
    
    rec = {VALUE_OF_OPERATION_NAME: opName, 
           VALUE_OF_AUDIO_NAME: audioName,
           VALUE_OF_AUDIO_DURATION: audioDuration,
           VALUE_OF_AUDIO_REAL_DURATION: audioRealDuration,
           VALUE_OF_LIGHT_DELAY: lightDelay,
           VALUE_OF_LIGHT_POWER: lightPower}
    testSteps[key] = rec;
    
    i = i + 1

"""
Ckeck Configurations
"""

# NotUsed Right Now, implemented later
#sorted(testSteps.keys())
#testSteps = sorted(testSteps.items(), key=lambda d:d[0], reverse = False)
#print(testSteps)
#sorted(testSteps.keys(), key=lambda d:d[0], reverse = False)
#print(testSteps)

"""
Test PreEstimations
"""
oneRoundTestTimeInSeconds = 0.0
for key in testSteps:
    rec = testSteps[key]
    if (0 == rec[VALUE_OF_AUDIO_DURATION]):
        duration = rec[VALUE_OF_AUDIO_REAL_DURATION]
    rec_seconds = duration + rec[VALUE_OF_LIGHT_DELAY]
    oneRoundTestTimeInSeconds = oneRoundTestTimeInSeconds + \
                                     rec_seconds + \
                                     intervalOfTestSteps

overallTestTimeInSeconds = oneRoundTestTimeInSeconds * numOfTestLoops

print("Test Time Estimation:")
print("Test Time Estimation:", file=logfile)

print("One round test cost %f seconds."%oneRoundTestTimeInSeconds)
print("One round test cost %f seconds."%oneRoundTestTimeInSeconds, file=logfile)

print("Repeat one round test for %d times."%numOfTestLoops)
print("Repeat one round test for %d times."%numOfTestLoops, file=logfile)

print("Overall test cost %f. seconds."% overallTestTimeInSeconds)
print("Overall test cost %f. seconds."% overallTestTimeInSeconds, file=logfile)

time_takes = cal_estimate_time(overallTestTimeInSeconds)
print("It estimated %s."%time_takes)
print("It estimated %s."%time_takes, file=logfile)

overallTestTimeRemainedInSeconds = overallTestTimeInSeconds
print("=======================================")
print("=======================================", file=logfile)


"""
Test check
"""
yes_or_no = ask_yes_no("Please input 'y' or 'n' for continue or abort the test:")
if yes_or_no == 'n':
    sys.exit(0)

"""
Binary structure
"""


### Req
# to be added later

### Rsp
rspFormat      = ''

sAt            = struct.Struct('%ss'%LEN_OF_RSP_AT)
sModel         = struct.Struct('%ss'%LEN_OF_RSP_MODEL)
sStar1         = struct.Struct('%ss'%LEN_OF_RSP_STAR)
sAddress       = struct.Struct('%ss'%LEN_OF_METER_SN)

rspFormat      = '%ss'%LEN_OF_RSP_AT + \
                 '%ss'%LEN_OF_RSP_MODEL + \
                 '%ss'%LEN_OF_RSP_STAR + \
                 '%ss'%LEN_OF_METER_SN

sTotalKWh      = struct.Struct('%ss'%LEN_OF_RSP_KWH)
sT1KWh         = struct.Struct('%ss'%LEN_OF_RSP_KWH)
sT2KWh         = struct.Struct('%ss'%LEN_OF_RSP_KWH)
sT3KWh         = struct.Struct('%ss'%LEN_OF_RSP_KWH)
sT4KWh         = struct.Struct('%ss'%LEN_OF_RSP_KWH)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_KWH + \
                 '%ss'%LEN_OF_RSP_KWH + \
                 '%ss'%LEN_OF_RSP_KWH + \
                 '%ss'%LEN_OF_RSP_KWH + \
                 '%ss'%LEN_OF_RSP_KWH

sTotalRevKWh   = struct.Struct('%ss'%LEN_OF_RSP_KWH)
sT1RevKWh      = struct.Struct('%ss'%LEN_OF_RSP_KWH)
sT2RevKWh      = struct.Struct('%ss'%LEN_OF_RSP_KWH)
sT3RevKWh      = struct.Struct('%ss'%LEN_OF_RSP_KWH)
sT4RevKWh      = struct.Struct('%ss'%LEN_OF_RSP_KWH)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_KWH + \
                 '%ss'%LEN_OF_RSP_KWH + \
                 '%ss'%LEN_OF_RSP_KWH + \
                 '%ss'%LEN_OF_RSP_KWH + \
                 '%ss'%LEN_OF_RSP_KWH

sV1Voltage     = struct.Struct('%ss'%LEN_OF_RSP_VOLTAGE)
sV2Voltage     = struct.Struct('%ss'%LEN_OF_RSP_VOLTAGE)
sV3Voltage     = struct.Struct('%ss'%LEN_OF_RSP_VOLTAGE)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_VOLTAGE + \
                 '%ss'%LEN_OF_RSP_VOLTAGE + \
                 '%ss'%LEN_OF_RSP_VOLTAGE

sA1Current     = struct.Struct('%ss'%LEN_OF_RSP_CURRENT)
sA2Current     = struct.Struct('%ss'%LEN_OF_RSP_CURRENT)
sA3Current     = struct.Struct('%ss'%LEN_OF_RSP_CURRENT)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_CURRENT + \
                 '%ss'%LEN_OF_RSP_CURRENT + \
                 '%ss'%LEN_OF_RSP_CURRENT

sPower1        = struct.Struct('%ss'%LEN_OF_RSP_POWER)
sPower2        = struct.Struct('%ss'%LEN_OF_RSP_POWER)
sPower3        = struct.Struct('%ss'%LEN_OF_RSP_POWER)
sPowerTotal    = struct.Struct('%ss'%LEN_OF_RSP_POWER)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_POWER + \
                 '%ss'%LEN_OF_RSP_POWER + \
                 '%ss'%LEN_OF_RSP_POWER + \
                 '%ss'%LEN_OF_RSP_POWER

sCos1          = struct.Struct('%ss'%LEN_OF_RSP_COS)
sCos2          = struct.Struct('%ss'%LEN_OF_RSP_COS)
sCos3          = struct.Struct('%ss'%LEN_OF_RSP_COS)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_COS + \
                 '%ss'%LEN_OF_RSP_COS + \
                 '%ss'%LEN_OF_RSP_COS

sMaxDmd        = struct.Struct('%ss'%LEN_OF_RSP_MAX_DMD)
sStar2         = struct.Struct('%ss'%LEN_OF_RSP_STAR)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_MAX_DMD + \
                 '%ss'%LEN_OF_RSP_STAR

sTime          = struct.Struct('%ss'%LEN_OF_RSP_TIME)
sCt            = struct.Struct('%ss'%LEN_OF_RSP_CT)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_TIME + \
                 '%ss'%LEN_OF_RSP_CT

sPulse1Count   = struct.Struct('%ss'%LEN_OF_RSP_PULSE_COUNT)
sPulse2Count   = struct.Struct('%ss'%LEN_OF_RSP_PULSE_COUNT)
sPulse3Count   = struct.Struct('%ss'%LEN_OF_RSP_PULSE_COUNT)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_PULSE_COUNT + \
                 '%ss'%LEN_OF_RSP_PULSE_COUNT + \
                 '%ss'%LEN_OF_RSP_PULSE_COUNT

sPulse1Ratio   = struct.Struct('%ss'%LEN_OF_RSP_PULSE_RATIO)
sPulse2Ratio   = struct.Struct('%ss'%LEN_OF_RSP_PULSE_RATIO)
sPulse3Ratio   = struct.Struct('%ss'%LEN_OF_RSP_PULSE_RATIO)
sPulseHL       = struct.Struct('%ss'%LEN_OF_RSP_PULSE_HL)

rspFormat      = rspFormat + \
                 '%ss'%LEN_OF_RSP_PULSE_RATIO + \
                 '%ss'%LEN_OF_RSP_PULSE_RATIO + \
                 '%ss'%LEN_OF_RSP_PULSE_RATIO + \
                 '%ss'%LEN_OF_RSP_PULSE_HL

sReserve20     = struct.Struct('%ss'%LEN_OF_RSP_RESERVE)

rspFormat      = rspFormat + '%ss'%LEN_OF_RSP_RESERVE

sEnd           = struct.Struct('%ss'%LEN_OF_RSP_END)
sCrc           = struct.Struct('%ss'%LEN_OF_RSP_CRC)

rspFormat      = rspFormat + '%ss'%LEN_OF_RSP_END + '%ss'%LEN_OF_RSP_CRC

rspLen = sAt.size + sModel.size + sStar1.size + sAddress.size
rspLen = rspLen + sTotalKWh.size + sT1KWh.size + sT2KWh.size + sT3KWh.size + sT4KWh.size
rspLen = rspLen + sTotalRevKWh.size + sT1RevKWh.size + sT2RevKWh.size + sT3RevKWh.size + sT4RevKWh.size
rspLen = rspLen + sV1Voltage.size + sV2Voltage.size + sV3Voltage.size
rspLen = rspLen + sA1Current.size + sA2Current.size + sA3Current.size
rspLen = rspLen + sPower1.size + sPower2.size + sPower3.size + sPowerTotal.size
rspLen = rspLen + sCos1.size + sCos2.size + sCos3.size
rspLen = rspLen + sMaxDmd.size + sStar2.size
rspLen = rspLen + sTime.size
rspLen = rspLen + sCt.size + sPulse1Count.size + sPulse2Count.size + sPulse3Count.size
rspLen = rspLen + sPulse1Ratio.size + sPulse2Ratio.size + sPulse3Ratio.size + sPulseHL.size
rspLen = rspLen + sReserve20.size + sEnd.size
rspLen = rspLen + sCrc.size

"""
Begin Testing ...
"""
if (softwareSimulation):
    print("Simulation started...")
    print("Simulation started...", file=logfile)
else:
    print("Test started...")
    print("Test started...", file=logfile)
    ser = serial.Serial()
    port_open(ser, serialPort)
    
i = 1
while i <= numOfTestLoops:
    now_time     = datetime.datetime.now()
    str_now_time = now_time.strftime('%Y-%m-%d %H:%M:%S')
    
    print("%s ==> %d loop"%(str_now_time, i))
    print("%s ==> %d loop"%(str_now_time, i), file=logfile)
    
    print("%d(remained seconds)/%d(total seconds)"%(overallTestTimeRemainedInSeconds, overallTestTimeInSeconds))
    print("%d(remained seconds)/%d(total seconds)"%(overallTestTimeRemainedInSeconds, overallTestTimeInSeconds), file=logfile)
    
    #for key in testSteps:
    k = 1
    while k <= numOfTestSteps:
        print("+++")
        print("+++", file=logfile)
        
        if (1 != k):
            # step interval for break
            time.sleep(intervalOfTestSteps)
        
        key = SECTION_OF_TEST_STEPS_PREFIX + '%02d' % k
        k = k + 1
        
        now_time     = datetime.datetime.now()
        str_now_time = now_time.strftime('%Y-%m-%d %H:%M:%S')
        
        print("%s ==> %s"%(str_now_time, key))
        print("%s ==> %s"%(str_now_time, key), file=logfile)
        rec = testSteps[key]
        
        # Test step actions in record.
        print(rec)
        print(rec, file=logfile)
        
        # Audio file brocast for the smart speaker
        if (0 == rec[VALUE_OF_AUDIO_DURATION]):
            cmdOption = "%s"%sPlayerOption
            simAudioDuration = rec[VALUE_OF_AUDIO_REAL_DURATION]
        else:
            cmdOption = "%s -endpos %d"%(sPlayerOption, rec[VALUE_OF_AUDIO_DURATION]) 
            simAudioDuration = rec[VALUE_OF_AUDIO_DURATION]
        
        if (softwareSimulation):
            print("SIMU: paly %s\%s"%(audioPath, rec[VALUE_OF_AUDIO_NAME]))
            print("SIMU: paly %s\%s"%(audioPath, rec[VALUE_OF_AUDIO_NAME]), file=logfile)
            print("SIMU: audio play duration for %d seconds"%simAudioDuration)
            print("SIMU: audio play duration for %d seconds"%simAudioDuration, file=logfile)
            time.sleep(simAudioDuration)
        else:
            if blPlayerInternal:
                print("INTERNAL: paly %s\%s"%(audioPath, rec[VALUE_OF_AUDIO_NAME]))
                print("INTERNAL: paly %s\%s"%(audioPath, rec[VALUE_OF_AUDIO_NAME]), file=logfile)
                mixer.init()
                mixer.music.load("%s\%s"%(audioPath, rec[VALUE_OF_AUDIO_NAME]))
                mixer.music.play()
                time.sleep(simAudioDuration)
            else:
                cmd = "%s\%s %s %s\%s"%(sPlayerPath, 
                                        sPlayerName, 
                                        cmdOption, 
                                        audioPath, 
                                        rec[VALUE_OF_AUDIO_NAME])
                print(cmd)
                print(cmd, file=logfile)
                fp=os.popen(cmd) 
                fpread=fp.read()
                print("%s"%fpread)
                print("%s"%fpread, file=logfile)

        time.sleep(rec[VALUE_OF_LIGHT_DELAY])
        
        # SourceMeter measurement
        if (softwareSimulation):
            print("SIMU: power should be %d"%rec[VALUE_OF_LIGHT_POWER])
            print("SIMU: power should be %d"%rec[VALUE_OF_LIGHT_POWER], file=logfile)
            trd = TestRecord(key, True, rec[VALUE_OF_LIGHT_POWER], rec[VALUE_OF_LIGHT_POWER])
            
            blResult = True  
            rand = random.random()
            if (rand > 0.5):
                blResult = False;
                print("SIMU: Radom(%f) Result Failed."%rand)
                print("SIMU: Radom(%f) Result Failed."%rand, file=logfile)
            else:
                print("SIMU: Radom(%f) Result Passed."%rand)
                print("SIMU: Radom(%f) Result Passed."%rand, file=logfile)
        else:
            # serial get power should be implemented here.            
            bCmdPrefix  = METER_CMD_PREFIX
            bCmdSuffix  = METER_CMD_SURFIX
            bCmdMeterSn = meterSn.encode()
            
            lCmdPrefix  = len(bCmdPrefix)
            lCmdSuffix  = len(bCmdSuffix)
            lCmdMeterSn = len(bCmdMeterSn)
                
            lprotoCmd   = lCmdPrefix + lCmdSuffix + lCmdMeterSn
            
            sCmdPrefix  = struct.Struct('!%ds'%lCmdPrefix)
            sCmdSuffix  = struct.Struct('!%ds'%lCmdSuffix)
            sCmdMeterSn = struct.Struct('!%ds'%LEN_OF_METER_SN)
            
            sCmdSize = sCmdPrefix.size + sCmdSuffix.size + sCmdMeterSn.size
            
            protoBuffer = ctypes.create_string_buffer(sCmdSize)
            #print('Before :',binascii.hexlify(protoBuffer))
            
            sCmdPrefix.pack_into(protoBuffer,0,bCmdPrefix)
            #print('Prefix :',binascii.hexlify(protoBuffer))
            
            aMeterSn = bytearray(LEN_OF_METER_SN)
            j = 0
            while j < LEN_OF_METER_SN:
                if (j >= LEN_OF_METER_SN - lCmdMeterSn):
                    aMeterSn[j] = bCmdMeterSn[j - LEN_OF_METER_SN + lCmdMeterSn]
                    #print("j = %d, array = 0x%x"%(j,aMeterSn[j]))
                j = j + 1
            
            sCmdMeterSn.pack_into(protoBuffer,sCmdPrefix.size,aMeterSn)
            #print('MeterSn :',binascii.hexlify(protoBuffer))
            
            sCmdSuffix.pack_into(protoBuffer,sCmdPrefix.size + LEN_OF_METER_SN,bCmdSuffix)
            print('Suffix :',binascii.hexlify(protoBuffer))
            print('Suffix :',binascii.hexlify(protoBuffer), file=logfile)
            
            # serial send command to SourceMeter      
            blResult = send(protoBuffer)
            if (blResult):
                print('ReqBuffer(S) : %s'%(binascii.hexlify(protoBuffer)))
                print('ReqBuffer(S) : %s'%(binascii.hexlify(protoBuffer)), file=logfile)
            else:
                print('ReqBuffer(F) : %s'%(binascii.hexlify(protoBuffer)))
                print('ReqBuffer(F) : %s'%(binascii.hexlify(protoBuffer)), file=logfile)
            
            # serial get respond from SourceMeter 
            #rspBuffer = ser.readline()
            count = 0
            while count < rspLen:
                count = ser.inWaiting() 

            rspBuffer = ser.read(count) 
            print('rspBuffer: %s'%(binascii.hexlify(rspBuffer)))
            print('rspBuffer: %s'%(binascii.hexlify(rspBuffer)), file=logfile)      
            
            # parse hex readings and extract power reading indication
            #print("rspBuffer len = ", len(rspBuffer))
            #hex_show(rspBuffer, logfile)    
            rspAck = struct.unpack(rspFormat, rspBuffer)
            print(rspAck)
            print(rspAck, file=logfile)
            
            bPower = rspAck[INDEX_OF_SOURCE_METER_TOTAL_POWER]
            sPower = bytes.decode(bPower)
            iPower = int(sPower)
            
            iRes = IsValuePass(iPower,rec[VALUE_OF_LIGHT_POWER],powerAccuracy,powerTolerance)
            
            if (0 == iRes):
                blResult = True
            else:
                blResult = False
            
            trd = TestRecord(key, blResult, rec[VALUE_OF_LIGHT_POWER], iPower)

            if (blResult):
                print("TEST: %s (%d/%d) Passed."%(rec[VALUE_OF_OPERATION_NAME], iPower, rec[VALUE_OF_LIGHT_POWER]))
                print("TEST: %s (%d/%d) Passed."%(rec[VALUE_OF_OPERATION_NAME], iPower, rec[VALUE_OF_LIGHT_POWER]), file=logfile)
            else:
                print("TEST: %s (%d/%d) Failed(%d)."%(rec[VALUE_OF_OPERATION_NAME], iPower, rec[VALUE_OF_LIGHT_POWER],iRes))
                print("TEST: %s (%d/%d) Failed(%d)."%(rec[VALUE_OF_OPERATION_NAME], iPower, rec[VALUE_OF_LIGHT_POWER],iRes), file=logfile)

        trt.result_add(key, blResult, trd)
        
        overallTestTimeRemainedInSeconds = overallTestTimeRemainedInSeconds - \
            simAudioDuration - rec[VALUE_OF_LIGHT_DELAY]
            
        verbose_ping_ex(pingAddress, logfile)
        overallTestTimeRemainedInSeconds = overallTestTimeRemainedInSeconds - intervalOfTestSteps
            
    print("###")
    print("###", file=logfile)
    i = i + 1

"""
Test Summary ...
"""

trt.summary(logfile)

end_time     = datetime.datetime.now()
str_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
 
time_takes = cal_difftime(start_time, end_time)

print("It takes %s."%time_takes)
print("It takes %s."%time_takes, file=logfile)

if (softwareSimulation):
    print("Simulation end. %s"%str_end_time)
    print("Simulation end. %s"%str_end_time, file=logfile)
else:
    port_close(ser)
    print("Test end. %s"%str_end_time)
    print("Test end. %s"%str_end_time, file=logfile)

logfile.close()
