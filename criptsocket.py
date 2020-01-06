import socket as basesocket
from struct import pack, unpack, calcsize
from hashlib import sha512
from time import clock
#  Todo make this entire code on C
class socket(object):
	def __init__(self,key=None,mutatekey=True,jumper=0,jumperfunc=None,s=basesocket.socket(),hekey="",mekey=""):
		self.s = s
		self.mekey = mekey
		self.hekey = hekey
		self.key = key
		if key is not None:
			self.hekey = key
			self.mekey = key
		self.mutatekey = mutatekey
		self.jump = jumper
		if jumperfunc is None:
			self.jumperfunc = lambda ordk,position,lk,jump : (ordk * position + jump)%lk
		else:
			self.jumperfunc = jumperfunc
	def precise_recv(self,data):
		while True:
			if data == self.s.recv(1):
				return
	def cript(self,key,dat):
		#  Todo make this function in C
		kp = 0 #  Key position
		key = list(key)
		lk = len(key) -1 #  key length
		data = list(dat)
		range_data = len(data) -1
		position = 0
		while position <= range_data:
			dataord = ord(data[position])
			
			pos = self.jumperfunc(ord(key[kp]),position,lk,self.jump)
			
			data[position] = chr( dataord ^ ord(key[pos]))
			kp += 1
			if kp > lk:
				kp = 0
			
			"""try:
				key[kp]
			except:
				kp = 0
			"""
			position += 1
			
		return "".join(data)
	def send(self,data):
		self.s.send("\x50")
		self.s.recv(1)
		self.s.send(pack('<Q',len(data)+3))
		self.s.recv(1)
		self.s.send(self.cript(self.hekey,"\x00\xff\x55"+data))
		self.s.recv(1)
		if self.mutatekey:
			self.mekey = sha512(self.mekey+data[:3]).digest()
		self.s.recv(1)
		self.s.send("\x80")
		self.s.recv(1)
	def recv(self):
		self.precise_recv("\x50")
		self.s.send("\x00")
		size = unpack('<Q',self.s.recv(calcsize("<Q")))[0]
		data = ""
		recived = 0
		self.s.send("\x00")
		while recived < size:
			rec = self.s.recv(size)
			recived += len(rec)
			data += rec
		self.s.send("\x00")
		#print 'hekey = '+self.mekey.encode('hex')
		data = self.cript(self.mekey,data)
		if data[:3] != "\x00\xff\x55": raise Exception ('Key not equal')
		data = data[3:]
		
		if self.mutatekey:
			self.hekey = sha512(self.hekey + data[:3]).digest()
			
		self.s.send("\x01")
		self.precise_recv("\x80")
		self.s.send("\x01")
		return data
	def connect(self,value):
		print self.key
		self.s.connect(value)
		if self.key is None:
			self.mekey = sha512(str(clock())).digest()
			print self.mekey.encode("hex")
			self.s.send(self.mekey)
			self.hekey = self.cript(self.mekey,self.s.recv(128))
			print self.hekey.encode("hex")
		else:
			pass
	def bind(self,port):
		self.s.bind(("0.0.0.0",port))
	def listen(self,number):
		self.s.listen(number)
	def setup(self,conn,ip):
		print self.key
		if self.key is None:
			self.hekey = conn.recv(128)
			print self.hekey.encode("hex")
			self.mekey = sha512(self.hekey+str(ip)+str(clock())).digest()
			#self.mekey = sha512(str(clock())).digest()
			print self.mekey.encode("hex")
			conn.send(self.cript(self.hekey,self.mekey))
		else:
			pass
		return conn , ip
	def accept(self):
		conn , ip =self.s.accept()
		temps = self.s
		self.s = conn
		conn , ip = self.setup(conn,ip)
		self.s = temps
		return socket(key=self.key, mutatekey=self.mutatekey, jumper=self.jump, jumperfunc=self.jumperfunc,s=conn,hekey=self.hekey,mekey=self.mekey) , ip