import platform
import os
import uuid
import urllib2
import json
import traceback
import tempfile
import re
import getpass
import sys
import argparse
import random
#import telly
import robot_util
import serial
import time
import atexit
import sys
import thread
import subprocess
import datetime
from socketIO_client import SocketIO, LoggingNamespace

parser = argparse.ArgumentParser(description='start robot control program')
parser.add_argument('robot_id')
parser.add_argument('--tts-volume', type=int, default=80)
parser.add_argument('--speaker-device', type=int, default=2)
parser.add_argument('--reverse-ssh-key-file', default='/home/pi/reverse_ssh_key1.pem')
parser.add_argument('--reverse-ssh-host', default='ubuntu@52.52.204.174')

commandArgs = parser.parse_args()
print commandArgs

# watch dog timer
os.system("sudo modprobe bcm2835_wdt")

# Set volume levle
# tested for 3.5mm audio jack
os.system("amixer set PCM --100%d%%" % commandArgs.tts_volume)

# etsted for USB audio device
#os.system("amixer -c %d cset numid=3 %d%%" % (commandArgs.speaker_devie, commandArgs.tts_volume))

infoServer = 'letsrobot.tv'

tempDir = tempfile.gettempdir()
print "temporary directory: ", tempDir

serialDevice = '/dev/ttyACM0'

chargeIONumber = 17
robotID = commandArgs.robot_id

def getControlHostPort():
    url = 'https://%s/get_control_host_port/%s' % (infoServer, robotID)
    response = robot_util.getWithRetry(url, secure=True)
    return json.loads(response)

def getChatHostPort():
    url = 'https://%s/get_chat_host_port/%s' % (infoServer, robotID)
    response = robot_util.getWithRetry(url, secure=True)
    return json.loads(response)

controlHostPort = getControlHostPort()
chatHostPort = getChatHostPort()

print "connecting to control socket.io", controlHostPort
controlSocketIO = SocketIO(controlHostPort['host'], controlHostPort['port'], LoggingNamespace)
print "finished using socket io to connect to control host port", controlHostPort

print "connecting to chat socket.io", chatHostPort
chatSocket = SocketIO(chatHostPort['host'], chatHostPort['port'])
print "finished using socket io to connect too chat", chatHostPort

print "connecting to app server socket.io"
appServerSocketIO = SocketIO(infoServer, LoggingNamespace)
print "finished connecting to app server"

def isInternetConnected():
    try:
        urllib2.urlopen('https://www.google.com', timeout = 1)
        return True
    except urllib2.URLError as err:
        return False

def processWoot(username, amount):
    print 'woot!! username: ', username, ' amount: ', amount

def handle_chat_message(args):
    rawMessage = args['message']
    withoutName = rawMessage.split(']')[1:]
    message = "".join(withoutName)
    urlRegExp = "(http|ftp|https)://([\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
    if message[1] == ".":
        exit()
    else:
        say(message)

def handle_command(args):
    global handlingCommand

    if 'robot_id' in args and args['robot_id'] == robotID: print 'received message:', args
        # Note if you are adding features to your bot, you can get direct access to incoming commands right here

    if 'command' in args and 'robot_id' in args and args['robot_id'] == robotID:
        print('got command', args)

        command = args['command']
        if command in ('y','h,','u','j','i','k','n','m','z','x'):
            robot_util.sendSerialCommand(ser, command)

def handleStartReverseSshProcess(args):
    print "starting reverse ssh"
    appServerSocketIO.emit("reverse_ssh_info", "starting")

    returnCode = subprocess.call(["/usr/bin/ssh",
                                  "-X",
                                  "-i", commandArgs.reverse_ssh_key_file,
                                  "-N",
                                  "-R", "2222:localhost:22",
                                  commandArgs.reverse_ssh_host])

    appServerSocketIO.emit("reverse_ssh_info", "return code: " + str(returnCode))
    print "reverse ssh process has exited with code", str(returnCode)

def handleEndReverseSshProcess(args):
    print "handling end reverse ssh process"
    resultCode = subprocess.call(["killall","ssh"])
    print "result code of killall ssh:", resultCode

def onHandleCommand(*args):
    thread.start_new_thread(handle_command, args)

def onHandleChatMessage(*args):
    thread.start_new_thread(handle_chat_message, args)

processing = []
deleted = []
def onHandleChatMessageRemoved(*args):
    if args[0]['message_id'] in processing and args[0] not in deleted:
        deleted.append(args[0]['message_id'])

def onHandleAppServerConnect(*args):
    print
    print "chat socket.io connect"
    print
    identifyRobotID()

def onHandleAppServerReconnect(*args):
    print
    print "app server socket.io reconnect"
    print
    identifyRobotID()

def onHandleAppServerDisconnect(*args):
    print
    print "app server socket.io disconnect"
    print

def onHandleChatConnect(*args):
    print
    print "chat socket.io connect"
    print
    identifyRobotID()

def onHandleChatReconnect(*args):
    print
    print "chat socket.io reconnect"
    print
    identifyRobotID()
    
def onHandleChatDisconnect(*args):
    print
    print "chat socket.io disconnect"
    print
    
def onHandleControlDisconnect(*args):
    print
    print "control socket.io disconnect"
    print
    newControlHostPort = getControlHostPort() #Reget control port will start if it closed for whatever reason
    if controlHostPort['port'] != newControlHostPort['port']: #See if the port is not the same as before
	print "restart: control host port changed"
	sys.exit(1) #Auto restart script will restart if the control port is not the same (which is unlikely)

#from communication import socketIO
controlSocketIO.on('command_to_robot', onHandleCommand)
controlSocketIO.on('disconnect', onHandleControlDisconnect)

appServerSocketIO.on('exclusive_control', onHandleExclusiveControl)
appServerSocketIO.on('connect', onHandleAppServerConnect)
appServerSocketIO.on('reconnect', onHandleAppServerReconnect)
appServerSocketIO.on('disconnect', onHandleAppServerDisconnect)

def startReverseSshProcess(*args):
   thread.start_new_thread(handleStartReverseSshProcess, args)

def endReverseSshProcess(*args):
   thread.start_new_thread(handleEndReverseSshProcess, args)

appServerSocketIO.on('reverse_ssh_8872381747239', startReverseSshProcess)
appServerSocketIO.on('end_reverse_ssh_8872381747239', endReverseSshProcess)

def ipInfoUpdate():
    appServerSocketIO.emit('ip_information',
                  {'ip': subprocess.check_output(["hostname", "-I"]), 'robot_id': robotID})

def identifyRobotID():
    """Tells the server which robot is using the connection"""
    print "sending identy robot id messages"
    chatSocket.emit('identify_robot_id', robotID)
    appServerSocketIO.emit('identify_robot_id', robotID)

waitCounter = 0

if platform.system() == 'Darwin':
    pass
    #ipInfoUpdate()
elif platform.system() == 'Linux':
    ipInfoUpdate()


lastInternetStatus = False


def waitForAppServer():
    while True:
        appServerSocketIO.wait(seconds=1)

def waitForControlServer():
    while True:
        controlSocketIO.wait(seconds=1)        

def waitForChatServer():
    while True:
        chatSocket.wait(seconds=1)

def waitForUserServer():
    while True:
        userSocket.wait(seconds=1)

def startListenForAppServer():
   thread.start_new_thread(waitForAppServer, ())

def startListenForControlServer():
   thread.start_new_thread(waitForControlServer, ())

def startListenForChatServer():
   thread.start_new_thread(waitForChatServer, ())

def startListenForUserServer():
    thread.start_new_thread(waitForUserServer, ())


startListenForControlServer()
startListenForAppServer()

startListenForChatServer()
startListenForUserServer()

while True:
    time.sleep(1)

    if (waitCounter & 1000) == 0:
        internetStatus = isInternetConnected()
        if internetStatus != lastInternetStatus:
            if internetStatus:
                say("ok")
            else:
                say("missing internet connection")
        lastInternetStatus = internetStatus

    if (waitCounter % 60) == 0:
        if platform.system() == 'Linux':
            ipInfoUpdate()

    waitCounter += 1