import cv2
import threading
import time
import logging

import zmq
import base64
import numpy as np

logger = logging.getLogger(__name__)

thread = None

class Camera:
	def __init__(self,fps=1024,video_source=0):
		logger.info(f"Initializing camera class with {fps} fps and video_source={video_source}")
		self.fps = fps
		self.video_source = video_source
		self.camera = None
		self.max_frames = 3 #1*self.fps
		self.frames = []
		self.isrunning = False
	def run(self):
		logging.debug("Perparing thread")
		global thread
		if thread is None:
			logging.debug("Creating thread")
			thread = threading.Thread(target=self._capture_incoming_feed,daemon=True)
			logger.debug("Starting thread")
			self.isrunning = True
			thread.start()
			logger.info("Thread started")

	def _capture_loop(self):
		dt = 1/self.fps
		logger.debug("Observation started")
		while self.isrunning:
			v,im = self.camera.read()
			if v:
				if len(self.frames)==self.max_frames:
					self.frames = self.frames[1:]
				self.frames.append(im)
			#time.sleep(dt)
		logger.info("Thread stopped successfully")

	def stop(self):
		logger.debug("Stopping thread")
		self.isrunning = False

	def get_frame(self, _bytes=True):
		if len(self.frames)>0:
			if _bytes:
				#logger.debug("Second encode")
				img = cv2.imencode('.jpeg',self.frames[-1])[1].tobytes()
			else:
				img = self.frames[-1]
		else:
			with open("images/not_found.jpeg","rb") as f:
				img = f.read()
		return img

	def _capture_incoming_feed(self):
		logger.debug("Icoming capture started")
		context = zmq.Context()
		socket = context.socket(zmq.SUB)
		socket.bind('tcp://*:7777')
		socket.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))
		dt = 1/self.fps
		while self.isrunning:
		     image_string = socket.recv_string()
		     raw_image = base64.b64decode(image_string)
		     image = np.frombuffer(raw_image, dtype=np.uint8)
		     if len(self.frames)==self.max_frames:
			     self.frames = self.frames[1:]
		     self.frames.append(cv2.imdecode(image, 1))
		     time.sleep(dt)
		logger.info("Thread stopped incoming feed successfully")
