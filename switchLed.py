occupiedPin = None
unoccupiedPin = None

# Demonstrates a custom script that is run upon an event being received
# The .ini file section for the GPIO sensor should contain for example:
# EventDetection: BOTH
# StateCallback: switchLed
# StateCallbackArgs: Actuator_Occupied,Actuator_Unccupied
def init(params):
    global occupiedPin
    global unoccupiedPin
    
    occupiedPin, unoccupiedPin = params('StateCallbackArgs').split(',')

def stateChange(state, params, actuators):
    global occupiedPin
    global unoccupiedPin
    
    # print(state)
    
    if (state != 1):
        actuators[occupiedPin].on_direct_message("ON")
        actuators[unoccupiedPin].on_direct_message("OFF")
    else:
        actuators[occupiedPin].on_direct_message("OFF")
        actuators[unoccupiedPin].on_direct_message("ON")
