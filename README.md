# huetemperature
Reads temperature from DS18B20 sensor and displays it on a 4-digit 7-segment display and by adjusting the color of a Philips Hue lamp.

This is written to run on Raspberry Pi Zero W that is connected to the same wireless network with the Hue gateway. 

To use this, create a localsettings.py file that contains your own API key, gateway URL and path to Dallas 1-wire sensor. 

If you want to use the huetemperature as a systemd service, put the .service file in /lib/systemd/system/ folder and the .py files in /opt/huetemperature/ folder. 
Then run:
sudo systemctl start huetemperature

To launch it always on boot, enable it: 
sudo systemctl enable huetemperature
