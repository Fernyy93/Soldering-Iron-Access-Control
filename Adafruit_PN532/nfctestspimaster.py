## NFC Access project for QUT EESS and Technical services
## Author: Alexander Fernicola

# import ID card reader library
import PN532

# timer libraries
import sys
import threading
import time

# URL request library
import requests

# import GPIO
import RPi.GPIO as GPIO

# convert byte array to string
import binascii

# Email libraries
import smtplib
import email
from email import utils
from email.mime.text import MIMEText
import datetime

# timer class
class Timer(threading.Thread):

	def __init__(self, maxtime, expire, inc=None, update=None):

		"""
		@param maxtime: time in seconds before timer expires
		@param expire: function called when timer expires
		@param inc: amount of time timer increments before updating in seconds, default is maxtime/2
		@param update: function called when timer updates
		"""

		self.maxtime=maxtime
		self.expire=expire
		if inc:
			self.inc=inc
		else:
			self.inc=maxtime/2
		if update:
			self.update=update
		else:
			self.update=lambda c : None
		self.counter=0
		self.active=False
		self.stop=False
		threading.Thread.__init__(self)
		self.setDaemon(True)

	def set_counter(self,t):
		
		"""
		set self.counter to t.
		"""
		
		self.counter=t

	def deactive(self):
		"""
		set self.active to false
		deactivates timer
		"""
		self.stop=True

	def reset(self):
		"""
		sets counter to 0, sets active to true, resets timer loop
		"""
		self.counter=0
		self.active=True

	def run(self):
		"""
		main timer loop
		"""
		
		while True:
			self.counter=0
			while self.counter < self.maxtime:
				self.counter+=self.inc
				time.sleep(self.inc)
				
				print(self.counter)
			if self.stop:
				return
			if self.active:
				self.update(self.counter)
		if self.active:
			self.expire()
			self.active=False

# CardReader class
class CardReader():
	def __init__(self, CS, SCLK, MOSI, MISO, device_id):
		"""
		@params CS, chip select pin
		@params SCLK, clock pin
		@params MOSI, master out slave in pin
		@params MISO, master in slave out pin
		a software based spi algorithm in the included libraries is used rather than hardware based spi
		@ params device_id, id of card reader assigned to room and soldering iron
		"""

		# instantiate instance of timer class
		self.timer=Timer(10, self.command, inc=1, update=self.relay_OFF)
		#instantiate instance of pn532 class
		pn532=PN532.PN532(cs=CS, sclk=SCLK, mosi=MOSI, miso=MISO)
		
		# start card reader
		pn532.begin()

		pn532.SAM_configuration()
		self.device_id = device_id

		# initialize states of LED's and relay
		GPIO.output(RED, True)
		GPIO.output(GREEN, False)
		GPIO.output(RELAY, False)

		# add event detection for relay button
		GPIO.add_event_detect(18,GPIO.BOTH, callback=self.close_relay)

	def command(self, e=None):
		print("reader idle")
		# not sure if this function is necessary

	def read(self):
		# start timer for this reader
		self.timer.start()
		
		# detect card swipe
		uid = pn532.read_passive_target()

		# check if one exists before proceeding
		if uid:
			print(uid)
			
			# form a byte array for posting to url
			rfid = "".join("%02x" % b for b in uid)
			print(rfid)
			
			# dummy response variable
			response = "ACESS Granted"
			
			# real function that does url request
			# r = self.send_to_url(self.rfid, self.device_id)

			if r != "NONE FOUNDAccess Denied":
				self.relay_ON()
			else:
				print("Access was denied")
				self.relay_OFF()

	def send_to_url(self, uid, device_id):

		# query part of url
		query = "http://131.181.33.3/TS_EEI/RFIDAccess/req_access.php?"
		
		# combine query, uid and device into a string
		host = ' '.join([query,'rfid=',uid,'&','device_id=',device_id])

		# retrieve response from url
		r = requests.get(host)
		return r.strip

	def relay_ON(self, e=None):
		# when id card reader gets positive response, reset timer
		self.timer.reset()
		
		# turn RED LED OFF
		GPIO.output(RED,False)
		
		# turn GREEN LED ON
		GPIO.output(GREEN, True)

	def relay_OFF(self, e=None):
		
		# turn RED LED ON
		GPIO.output(RED, True)

		# turn GREEN LED OFF
		GPIO.output(GREEN, False)
		print("relay off")

	def close_relay(self, channel):
		# function that closes relay and turns off soldering iron
		if GPIO.intput(channel):
			print("Rising edge detected on pin" + channel)
			self.relay_OFF()
		else:
			print("Falling edge detected on pin" + channel)

# email class
class Email():
	def __init__(self, location = '', me = '', you = ''):

		# text file location
		self.location=location

		# set sender address
		self.me = me

		# set receiver address
		self.you=you
		
		# file pointer, open file
		fp = open(location,'r')
		# get the time
		nowdt = datetime.datetime.now()
		nowtuple = nowdt.timetuple()
		nowtimestamp = time.mktime(nowtuple)
		thetime = utils.formatdate(nowtimestamp)

		# contents of message
		text = MIMEText(fp.read())
		self.text = text
		message = text.get_payload()
		fp.close()

		# add headers
		self.text['To'] = you
		self.text['From'] = me
		self.text['Date'] = thetime
		self.text['Subject'] = self.device_id

		# add event detection for email button
		# the button may be abused against students who keep the area tidy
		GPIO.add_event_detetc(22,GPIO.BOTH, callback = self.send_email)
		
	def send_email(self,channel):
		if GPIO.intput(22):
			s = smtplib.SMTP('smtp.gmail.com:587')
			s.starttls()
			s.login(self.me,'password')
			s.sendmail(self.me, [self.you], self.text.as_string())

# global functions for sending bits to 7 segment display

def send_16_bits(bits_to_send):

	for i in reversed(range(0,15)):
		word = (1 << i)
		if ((bits_to_send & word) == 0):
			GPIO.output(SIN,False)
		else:
			GPIO.output(SIN,True)
			
			GPIO.output(SCLK, True)
			GPIO.output(SCLK, False)

def update_dual_7(new_display):

	num = {
		' ' : 0x00,
		'0' : 0x3F,
		'1' : 0x06,
		'2' : 0x5B,
		'3' : 0x4F,
		'4' : 0x66,
		'5' : 0x6D,
		'6' : 0x7D,
		'7' : 0x07,
		'8' : 0x7F,
		'9' : 0x6F
		}

	byte_hi = num[new_display[1]]
	byte_lo = num[new_display[0]]

	char_2_16 = (byte_hi << 8) + byte_lo
	
	send_16_bits(char_2_16)
	GPIO.output(LATCH, True)
	GPIO.output(LATCH, False)

# global macros for PIN numbers
RED = 11
GREEN = 13
RElAY = 15
RELAYBTTN = 16
SIN = 19
CLK = 21
EMAILBTTN = 22
LATCH = 25
BLANK = 26

CS = 18
MOSI = 23
MISO = 24
SCLK = 25

device_id1 = "S901_SOL001"
device_id2 = "S901_SOL002"

def main():
	
	# set GPIO mode to use physical pin numbers
	GPIO.setmode(GPIO.BOARD)
	
	# define pin directions
	GPIO.setup(RED, GPIO.OUT) # RED LED
	GPIO.setup(GREEN, GPIO.OUT) # GREEN LED
	GPIO.setup(RELAY, GPIO.OUT) # RELAY

	GPIO.setup(SIN, GPIO.OUT)
	GPIO.setup(CLK, GPIO.OUT)
	GPIO.setup(LATCH, GPIO.OUT)
	GPIO.setup(BLANK, GPIO.OUT)

	# intialize pins to default output

	# RED LED on
	GPIO.output(RED, False)
	# GREEN LED off
	GPIO.output(GREEN, False)
	# Relay closed, soldering iron off
	GPIO.output(RELAY, False)
	
	# shift register pins
	GPIO.output(SIN, False)
	GPIO.output(CLK, False)
	GPIO.output(LATCH, False)

	# clear display
	GPIO.output(BLANK, True)

	# setup button inputs
	GPIO.setup(EMAILBTTN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(RELAYBTTN, GPIO.IN, pull_up_down_GPIO.PUD_DOWN)

	Reader1 = CardReader(CS,MOSI,MISO,SCLK,device_id1)

	try:
		while True:
			Reader1.read()
	except KeyboardInterrupt:
		print("Manually terminated program")

	finally:
		GPIO.cleanup()

if __name__ == "__main__": main()
