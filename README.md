# "Laser" Gun Target Caster

### Purpose

Detect a red laser pointer on a surface and sends the picture to a Chromecast device on change.

More elaborately, this allows you to set up a target and "shoot" at it using a red laser pointer and view the resulting "impact point" on a Chromecast device, or old Android phone/tablet running something like [AirScreen](https://play.google.com/store/apps/details?id=com.ionitech.airscreen).

This allows me to do target practice with a modified airsoft gun with a laser pointer in it, from 10m away, in silence, and not have to get up to see where I hit, and not waste ammo or paper targets wastefully.

Also, friggin' laser beams!

### How It's Made

* A thread is started to detect as close as possible to the first appearance of a laser bead on a surface, using OpenCV
* A thread is started to act as a webserver for Chromecast content. This server always returns the contents of a file named `latest.jpg`, no matter what is asked for. The Chromecast device doesn't seem to refresh a file if it's told to show the same URL twice within a period of time.
* When a point has been detected, the frame gets written to disk as `latest.jpg`, also a signal is set
* When the signal is set, the main thread tells the Chromecast to show a new random image from the webserver started locally
* The Chromecast asks for the "new" uncached file, and gets served the latest impact capture

### Example

Install dependencies once:
`pip install numpy opencv-contrib-python pychromecast`

`python lasertarget.py --address 192.168.0.2 --port 8080 --index 2 --castto "Target Monitor"`

  * address/adapter and port of local webserver that will be created on the same computer this script is running on, has to be on the same network as Chromecast device (the device will pull content from this address).
  * index of camera device in OpenCV list, trial and error for now
  * castto the Chromecast device with this name

`python lasertarget.py`

  * starts a webserver using the default IP of the device being run on
  * uses the first camera device
  * will cast to the first device it finds, or just shows the preview window if none are found


### Tech Used

  * Modified version of [this OpenCV project](https://github.com/bradmontgomery/python-laser-tracker) for detecting the laser pointer
  (scalable window; trigger on change; only show first laser hit, not trail)
    * `pip install numpy opencv-contrib-python`
  * `HTTPServer` to serve the latest image regardless of client caching settings
  * [PyChromecast](https://github.com/balloob/pychromecast) to display the latest image on a Chromecast device
    * `pip install pychromecast`
