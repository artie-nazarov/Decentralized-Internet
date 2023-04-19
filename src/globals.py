from clocks import combine_clocks

#dicts that stores value, clock, and last writer
data = {}
data_clocks = {}
last_writer = {}

#dict that stores the most updated known clock for each value
known_clocks = {}

#list that stores the current view of the system
view = []

#int that stores the ID of the machine
id = -1

#address/ip
addr = ""

def update_known_clocks(new_clocks):
    """Takes a dict of keys/clocks and updates known_clocks to include them"""
    for key, clock in new_clocks.items():
        if key not in known_clocks:
            known_clocks[key] = clock
        else:
            combine_clocks(known_clocks[key], clock)