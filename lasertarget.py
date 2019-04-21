#! /usr/bin/env python

"""
    Purpose: Detect a red laser pointer on a surface and sends the picture to a Chromecast device on change.
    
    Uses:
        * Modified version of: https://github.com/bradmontgomery/python-laser-tracker for detecting the laser pointer
          (scalable window; trigger on change; only show first laser hit, not trail)
        * HTTPServer to serve the latest image regardless of client caching settings
        * PyChromecast to display the latest image on a Chromecast device
        
    Example:
        lasertarget.py --address 192.168.0.2 --port 8080 --index 2 --castto "Target Monitor"
        * address and port of local webserver on same network as Chromecast device
        * index of camera device in OpenCV list, trial and error for now
        * castto the Chromecast device with this name
"""

# built-in
import argparse
import time # to sleep
import threading
import socket # to get IP address
import queue
from http.server import BaseHTTPRequestHandler, HTTPServer

# 3rd party
import pychromecast

# local
from detection import LaserTracker


# WebServer stuff
class NoCacheServer(BaseHTTPRequestHandler):
	def do_GET(self):
		# No matter what the URL is, serve the same file, this helps get around client caching settings
		print("Got request for file [{}]...".format(self.path))
		self.send_response(200)
		self.send_header('Content-type', 'image/jpg')
		self.end_headers()
		with open('latest.jpg', 'rb') as file: 
			self.wfile.write(file.read()) # Read the file and send the contents 
			file.close()

def WebServerThread(address='127.0.0.1', port=8080):
	myServer = HTTPServer((address, port), NoCacheServer)
	myServer.serve_forever() # ...forever ever?

def StartWebServer(params):
    print("Starting web server for Chromecast on {}:{}...".format(params.address, params.port))
    daemon = threading.Thread(name='chromecastserver', target=WebServerThread, args=(params.address, params.port))
    daemon.setDaemon(True) # Set as a daemon so it will be killed once the main thread is dead.
    daemon.start()

    
# LaserTracker stuff
def LaserTrackerThread(params):
    tracker = LaserTracker(
        cam_width=params.width,
        cam_height=params.height,
        cam_zoom=params.zoom,
        hue_min=params.huemin,
        hue_max=params.huemax,
        sat_min=params.satmin,
        sat_max=params.satmax,
        val_min=params.valmin,
        val_max=params.valmax,
        display_thresholds=params.display,
        cam_index=params.index,
        detection_queue=params.queue
    )
    tracker.run()
    
def StartLaserTracker(params):    
    # start the thread
    print("Starting LaserTracker...")
    daemon = threading.Thread(name='lasertracker', target=LaserTrackerThread, args=(params, ))
    daemon.setDaemon(True) # Set as a daemon so it will be killed once the main thread is dead.
    daemon.start()
    
    
# main
def main(params):
    params.queue = queue.Queue()

    # try get the local IP if it wasn't provided
    if (params.address == ''):
        # https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            params.address = s.getsockname()[0]
        except:
            params.address = '127.0.0.1'
        finally:
            s.close()

    # try get the Chromecast if specified, or just use the first one if not
    chromecasts = pychromecast.get_chromecasts()
    cast = None
    if len(chromecasts) > 0:
        if (params.castto == ''):
            cast = chromecasts[0]
        else:
            for cc in chromecasts:
                if cc.device.friendly_name == params.castto:
                    cast = cc
                    break
            
    if cast:
        cast.wait()
        mc = cast.media_controller
        StartWebServer(params)
    else:
        print("! WARNING: could not find Chromecast !")
    
    StartLaserTracker(params)
    
    index = 0;
    print("Running...")
    while True:
        if not params.queue.empty():
            params.queue.get()
            print("File changed, refreshing...")
            index = index + 1 # Ensure it requests a new file that isn't in its cache
            url = "http://{}:{}/latest{}.jpg".format(params.address, params.port, index)
            print("New URL: {}".format(url))
            if (cast):
                mc.play_media(url, content_type = "image/jpg")
                mc.block_until_active()
                mc.play()
        time.sleep(0.2)
    

# parameters and bootstrap
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Laser Target Detector')
    parser.add_argument('-I', '--index',
                        default=0,
                        type=int,
                        help='Device Index of camera in OpenCV')
    parser.add_argument('-W', '--width',
                        default=640,
                        type=int,
                        help='Camera Width')
    parser.add_argument('-H', '--height',
                        default=480,
                        type=int,
                        help='Camera Height')
    parser.add_argument('-u', '--huemin',
                        default=20,
                        type=int,
                        help='Hue Minimum Threshold')
    parser.add_argument('-U', '--huemax',
                        default=160,
                        type=int,
                        help='Hue Maximum Threshold')
    parser.add_argument('-s', '--satmin',
                        default=100,
                        type=int,
                        help='Saturation Minimum Threshold')
    parser.add_argument('-S', '--satmax',
                        default=255,
                        type=int,
                        help='Saturation Maximum Threshold')
    parser.add_argument('-v', '--valmin',
                        default=200,
                        type=int,
                        help='Value Minimum Threshold')
    parser.add_argument('-V', '--valmax',
                        default=255,
                        type=int,
                        help='Value Maximum Threshold')
    parser.add_argument('-d', '--display',
                        action='store_true',
                        help='Display Threshold Windows')
    parser.add_argument('-A', '--address',
                        default='', # will be patched later with gethostbyname if not provided
                        type=str,
                        help='Local IP to serve Chromecast content on')
    parser.add_argument('-P', '--port',
                        default=8080,
                        type=int,
                        help='Local Port to serve Chromecast content on')
    parser.add_argument('-C', '--castto',
                        default='',
                        type=str,
                        help='Name of Chromecast device to cast to')
    parser.add_argument('-Z', '--zoom',
                        default=1,
                        type=int,
                        help='Zoom factor for capture window')
    params = parser.parse_args()

    main(params)