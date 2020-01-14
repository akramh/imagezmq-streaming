# USAGE
# python client.py --server-ip SERVER_IP

# import the necessary packages
from imutils.video import VideoStream
from imagezmq import imagezmq
import argparse
import socket
import time
import zmq

REQUEST_TIMEOUT = 2500


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--server-ip", required=True,
	help="ip address of the server to which the client will connect")
args = vars(ap.parse_args())

# initialize the ImageSender object with the socket address of the
# server
sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(
	args["server_ip"]))

poll = zmq.Poller()
poll.register(sender.zmq_socket,zmq.POLLIN)

# get the host name, initialize the video stream, and allow the
# camera sensor to warmup
rpiName = socket.gethostname()
vs = VideoStream(usePiCamera=False).start()
#vs = VideoStream(src=0).start()
time.sleep(2.0)
retries = 0
 
while True:
	# read the frame from the camera and send it to the server
	frame = vs.read()
	sender.send_image(rpiName, frame)

	socks = dict(poll.poll(REQUEST_TIMEOUT))
	if socks.get(sender.zmq_socket) == zmq.POLLIN:
		reply = sender.zmq_socket.recv()
		retries = 0
		if not reply:
			break
		
		# if reply == b'OK':
		# 	print("Server replied with ", reply)
		# else:
		# 	print("E: Malformed reply from server " % reply)

	else:
		retries += 1
		print("W: No response from server, retrying… ", retries)
		sender.zmq_socket.setsockopt(zmq.LINGER,0)
		sender.zmq_socket.close()
		poll.unregister(sender.zmq_socket)

		sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(args["server_ip"]))
		poll.register(sender.zmq_socket,zmq.POLLIN)


sender.zmq_context.term()