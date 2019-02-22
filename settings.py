import os.path 
from posixpath import join as urljoin 
from functools import reduce 

# NOTE: When configuring the temperature update interval, 
# remember to not read too often. Sensor does some 
# processing and would heat up a slightly.  
TEMPERATURE_UPDATE_INTERVAL = 30 # Default 30 secs.

# Don't make lamp update interval too small, temperature 
# may fluctuate on short term depending on the placement 
# of the sensor. Small inteval could make the light shift 
# its color back and forth notably. 
LAMP_UPDATE_INTERVAL = 300 # Default 5 minutes. 

# The following values work in test environment, override with 
# real values by creating localsettings.py and putting these there. 
HUE_GATEWAY_URL = "http://localhost"
LIGHT_ID = "1"
ONEWIRE_ADDRESS = "testsensor"
ONEWIRE_ROOT_PATH = "/tmp/testdevices/" 
HUE_API_KEY = "test" # Refer to HUE developer instructions.

# Now try to import all of the above from localsettings module, 
# Real values are in there, in settings.py we have just test settings. 
try: 
    from localsettings import *
except ImportError: 
    pass 

LAMP_URL = reduce(urljoin, (HUE_GATEWAY_URL, "api", HUE_API_KEY, "lights", LIGHT_ID, "state"))
SENSOR_FILE_PATH = os.path.join(ONEWIRE_ROOT_PATH, ONEWIRE_ADDRESS, "w1_slave")
