# ID card reader
import Adafruit_PN532 as PN532

# timer
import sys
import threading
import time

# URL requests
import requests

# GPIO
import RPi.GPIO as GPIO

import binascii

# EMAIL
import smtplib
import email
from email import utils
from email.mime.text import MIMEText
import datetime

# define pins
CS = 18
MOSI = 23
MISO = 24
SCLK = 25
GREEN = 2
RED = 3
RELAY = 4
EMAIL = 17
RELAY_B = 27


class Timer(threading.Thread):
	def __init__(self, maxtime, inc=None, update=None):

		self.maxtime=maxtime
		
		if inc:
			self.inc = inc
			
		else:
			self.inc=maxtime/2
		if update:
			self.update=update
		else:
			self.update=lambda c : relay_OFF()
		self.counter=0
		self.active=True
		self.stop=False
		threading.Thread.__init__(self)
		self.setDaemon(True)

	def set_counter(self,t):

		self.counter=t

	def deactivate(self):
		
		self.active=False

	def kill(self):

		self.stop=True

	def reset(self):

		self.counter=0
		self.active=True

	def run(self):

		while True:
			self.counter=0
			while self.counter < self.maxtime:
				self.counter+=self.inc
				time.sleep(self.inc)
				print self.counter
			if self.stop:
				return
			if self.active:
				self.update(self.counter)
		if self.active:
			self.active=False
			



def read(cardreader):
	
	timer.start()
	relay_OFF()
	while True:
		# check if card is available to read
		uid = cardreader.read_passive_target()
		if uid is None:
			print 'UID not found, trying again'
			continue
		print 'Found card with UID: 0x{0}'.format(binascii.hexlify(uid))
		
		# dummy response variable
		r = "ACCESS Granted"
		rfid = "".join("%02x" % b for b in uid)
		# real function calls send_to_url with RFID
		# r = send_to_url(rfid, device_id)

		if r != "NONE FOUNDAccess Denied":
			relay_ON()
		else:
			print("Access was denied")
			relay_OFF()

def send_to_url(uid, device_id):
	# query part of url
	query = "http://131.181.33.3/TS_EEI/RFIDAccess/req_access.php?"
	
	# object, unique to each PI?
	# device_id = "S901_SOL001"
	
	# combine query, uid and device
	host = ' '.join([query, 'rfid=',uid,'&','device_id=',device_id])

	# retrieve response from url
	r = requests.get(host)
	# print r.text
	# return response as string
	return r.strip

def relay_ON():
	GPIO.output(GREEN, True)
	GPIO.output(RED, False)
	GPIO.output(RELAY, True)
	timer.reset()

def relay_OFF():
	GPIO.output(GREEN, False)
	GPIO.output(RED, True)
	GPIO.output(RELAY, False)
	print 'Access was denied'
	timer.reset()

def relay_callback(channel):
	if GPIO.input(RELAY_B):
		print "Rising edge detected"
		relay_OFF()
	else:
		print "Falling edge detected"


def pins():
	# this function sets up pins
	# set GPIO mode to BCM mode
	GPIO.setmode(GPIO.BCM)

	# define pin directions
	GPIO.setup(RED, GPIO.OUT) # RED LED
	GPIO.setup(GREEN, GPIO.OUT) # GREEN LED
	GPIO.setup(RELAY, GPIO.OUT) # RELAY

	# initial states
	# RED LED on
	GPIO.output(RED, False)
	# Green LED off
	GPIO.output(GREEN, False)
	# Relay open
	GPIO.output(RELAY, False)

	# input buttons
	GPIO.setup(EMAIL, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(RELAY_B, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.add_event_detect(RELAY_B, GPIO.BOTH, callback = relay_callback)

timer = Timer(10, inc=1, update = None)

def main():

#	timer = Timer.Timer(10, command, inc=1, update = relay_OFF)
	if timer is None:
		print 'timer class not instantiated'

	# setup pins
	pins()
	
	# create card reader object
	pn532 = PN532.PN532(cs = CS, sclk = SCLK, mosi = MOSI, miso = MISO)

	pn532.begin()

	ic, ver, rev, support = pn532.get_firmware_version()
	print 'Found PN532 with firmware version: {0}.{1}'.format(ver, rev)

	pn532.SAM_configuration()
	print 'Waiting for MiFare card...'
	try:
		while True:			
			read(pn532)

	except KeyboardInterrupt:
		print 'Manually terminated program'

	finally:
		GPIO.cleanup()

if __name__ == "__main__": main()
