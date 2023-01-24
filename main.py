import json, os, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import jinja2
from boltiot import Bolt;
from twilio.rest import Client as Twilio

from app_config import *

## globals

data = []
device_online = False
file_lock = threading.Lock()

hostname = "localhost"
port = 80
development = True
terminate = False

## initialize

jenv = jinja2.Environment(loader=jinja2.FileSystemLoader("templates/"))
templates = {
	"home": jenv.get_template("home.jinja2")
}

device = Bolt(bolt_api_key, bolt_device_id)
twilio = Twilio(twilio_sid, twilio_key)
device.serialBegin(9600)

try:
	with open("room_data.json", mode="r", encoding="utf-8") as file:
		r_data = file.read()
		if (len(r_data) >= 2):
			data = json.loads(r_data)
except:
	data = []

## helper functions and classes

# returns index of apparent heat, 0 : safe, 4 : extreme danger
def heat_index(h, t):
	if t < 26: return 0
	if t > 43: return 4

	table = [
		[0, 0, 0, 0, 2, 2, 2],	# 0%
		[0, 0, 0, 2, 2, 2, 3],	# 10%
		[0, 0, 0, 2, 2, 3, 3],	# 20%
		[0, 0, 2, 2, 3, 3, 4],	# 30%
		[1, 1, 2, 3, 3, 4, 4],	# 40%
		[1, 1, 2, 3, 4, 4, 4],	# 50%
		[1, 1, 2, 3, 4, 4, 4],	# 60%
		[1, 1, 3, 4, 4, 4, 4],	# 70%
		[1, 2, 3, 4, 4, 4, 4],	# 80%
		[1, 3, 4, 4, 4, 4, 4],	# 90%
		[2, 3, 4, 4, 4, 4, 4]	# 100%
	]

	return table[h // 10][(t - 26) // 3]

# update data in json file
def write_file():
	global data

	file_lock.acquire()

	try:
		with open("room_data.json", mode="w", encoding="utf-8") as file:
			file.write(json.dumps(data))
	except Exception as e:
		print("::ERROR::FILE_WRITE::", e, sep="\n")
	
	file_lock.release()

# alert all contacts using twilio in case of danger
def alert_contacts(h_i, temp, humidity):
	for contact in twilio_contacts:
		twilio.messages.create(
			body=f"Alert, room heat index measured at {h_i}, current temperature at {temp} and humidity at {humidity}",
			from_= twilio_phone,
			to=contact
		)

# track room data using boltiot
def room_monitor():
	global device_online, data, terminate
	print("Listening for serial data fromt bolt device")

	t_counter = 0
	# read data from device every 5 minutes
	while True:
		# check for interrupts every 30 seconds
		if terminate: break
		time.sleep(30)
		t_counter += 1
		if t_counter < 10: continue

		t_counter = 0
		# update device status
		try:
			status = json.loads(device.isOnline())["value"]
			if status == "online": device_online = True
			else: device_online = False
		except Exception as e:
			print("::ERROR::BOLT::", e, sep="\n")
			device_online = False

		if not device_online: continue

		# update and save new sampled data
		res = json.loads(device.serialRead(ord("\n")))
		if res["success"] == 1 and len(res["value"]) >= 3:
			humidity, temp = map(float, res["value"].rstrip().split(" "))
			gmt_time = time.gmtime()
			data += [[
				[gmt_time.tm_mday, gmt_time.tm_hour, gmt_time.tm_min, gmt_time.tm_sec], 
				temp, 
				humidity
			]]
			threading.Thread(target=write_file).start()
			h_i = heat_index(humidity, temp)
			if h_i > 1:
				try:
					alert_contacts(h_i, temp, humidity)
				except Exception as e:
					print(e)

	print("room monitor thread terminated")

# main request handler
class ReqHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		global data

		ext = self.path.split(".")
		ext = ext[1] if len(ext) > 1 else ""
		if ext == "ico": return

		# main page
		if self.path == "/" or self.path == "/home/" or self.path == "/home":
			if development:
				templates["home"] = jenv.get_template("home.jinja2")

			self.send_response(200)
			self.send_header("Content-Type", "text/html")
			self.end_headers()
			self.wfile.write(bytes(templates["home"].render({
				"device_status": "online" if device_online else "offline"
			}), "utf-8"))

		# collected data
		elif self.path == "/data" or self.path == "/data/":
			self.send_response(200)
			self.send_header("Content-Type", "application/json")
			self.end_headers()
			self.wfile.write(bytes(json.dumps(data[max(len(data) - 100, 0):]), "utf-8"))
		
		# js scripts
		elif ext == "js":
			fPath = f"./public/scripts{self.path}"
			print(fPath)
			if os.path.isfile(fPath):
				with open(fPath, mode="r", encoding="utf-8") as file:
					self.send_response(200)
					self.send_header("Content-Type", "text/javascript")
					self.end_headers()
					self.wfile.write(bytes(file.read(), "utf-8"))
			
			else:
				self.send_response(404)
				self.send_header("Content-Type", "text/html")
				self.end_headers()
				self.wfile.write(bytes("Resource Not found", "utf-8"))
				
		# 404 not found
		else:
			self.send_response(404)
			self.send_header("Content-Type", "text/html")
			self.end_headers()
			self.wfile.write(bytes("Resource Not found", "utf-8"))

	def log_message(self, format, *args):
		pass
	
## main

if __name__ == "__main__":
	server = HTTPServer((hostname, port), ReqHandler)
	t1 = threading.Thread(target=room_monitor)
	t1.start()

	try:
		print(f"Server running at: http://{hostname}/{port}")
		server.serve_forever()
	except KeyboardInterrupt:
		terminate = True
		print("Server terminated")
		exit()