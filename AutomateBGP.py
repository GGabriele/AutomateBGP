from getpass import getpass
import os
import time
import argparse
import sys
import paramiko

CISCOTEMPLATE = """---
cisco_template:
   - { hostname: cisco_template, as: %s }

cisco_loopback:
"""
JUNIPERTEMPLATE = """
juniper_template:
   - { hostname: juniper_template, as: %s }

juniper_loopback:
"""
VYATTATEMPLATE = """
vyatta_template:
   - { hostname: vyatta_template, as: %s }

vyatta_loopback:
"""

CISCOLOOPBACK = "   - { name: %s, address: %s, network: %s, mask: %s }\n"
LOOPBACK = "   - { name: %s, address: %s, network: %s }\n"

NEIGHBORS = "   - { id: %s, as: %s }\n"
CISCONEIGHBORS = "\ncisco_neighbors:\n"
JUNIPERNEIGHBORS = "\njuniper_neighbors:\n"
VYATTANEIGHBORS = "\nvyatta_neighbors:\n"


def run_commands(ip_address, user, password, commandList, platform, buffer=5000):
    """ this function runs the specified commands on the node and returns a
    list with unfiltered results.
    """
    print "Configuring " + ip_address
    remote_conn_pre = paramiko.SSHClient()
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remote_conn_pre.connect(ip_address, username=user, password=password)
    remote_conn = remote_conn_pre.invoke_shell()
    if platform == "cisco":
        remote_conn.send("enable\n")
        time.sleep(1)
        remote_conn.send(password+'\n')
        time.sleep(1)
    commands = commandList.split('\n')
    for com in commands:
        remote_conn.send(com+'\n')
        time.sleep(1)
        output = remote_conn.recv(buffer)
        #print output

def CiscoLoopback():
    """ This function asks the user to insert information about loopback interfaces. """
    cisco = {}
    print "***Cisco router configuration***"
    as_number = raw_input("\tInsert BGP AS number: ")
    while True:
        cisco_loopback = {}
        loopback_name = raw_input("\tInsert loopback name (Press 'q' to quit): ")
        if loopback_name is not 'q':
            loopback_address = raw_input("\tLoopback address (eg. x.x.x.x): ")
            loopback_network = raw_input("\tLoopback network (eg. x.x.x.0): ")
            loopback_mask = raw_input("\tLoopback mask (eg. 255.255.255.0): ")
            cisco_loopback["address"] = loopback_address
            cisco_loopback["network"] = loopback_network
            cisco_loopback["mask"] = loopback_mask
            cisco[loopback_name] = cisco_loopback
        elif loopback_name == 'q':
            break
        else:
            print "You just typed something incorrect!"
    return (cisco, as_number)

def JuniperLoopback():
    """ This function asks the user to insert information about loopback interfaces. """
    print "***Juniper router configuration***"
    juniper = {}
    as_number = raw_input("\tInsert BGP AS number: ")
    count = 0
    while True:
        juniper_loopback = {}
        lo = raw_input("\tInsert loopback (Press any key to continue. Press 'q' to quit)")
        if lo is not 'q':
            count += 1
            loopback_address = raw_input("\tLoopback address (eg. x.x.x.x/x): ")
            loopback_network = raw_input("\tLoopback network (eg. x.x.x.0/x): ")
            juniper_loopback["address"] = loopback_address
            juniper_loopback["network"] = loopback_network
            juniper[count] = juniper_loopback
        else:
            break
    return (juniper, as_number)

def VyattaLoopback():
    """ This function asks the user to insert information about loopback interfaces. """
    print "***Vyatta router configuration***"
    vyatta = {}
    as_number = raw_input("\tInsert BGP AS number: ")
    count = 0
    while True:
        vyatta_loopback = {}
        lo = raw_input("\tInsert loopback (Press any key to continue. Press 'q' to quit)")
        if lo is not 'q':
            count += 1
            loopback_address = raw_input("\tLoopback address (eg. x.x.x.x/x): ")
            loopback_network = raw_input("\tLoopback network (eg. x.x.x.0/x): ")
            vyatta_loopback["address"] = loopback_address
            vyatta_loopback["network"] = loopback_network
            vyatta[count] = vyatta_loopback
        else:
            break
    return (vyatta, as_number)

def Neighbors(vendor):
    """ This function asks the user to insert information about BGP neighbors. """
    neighbors = {"cisco" : "", "juniper" : "", "vyatta" : "" }
    cisco_neighbors = {}
    juniper_neighbors = {}
    vyatta_neighbors = {}
    while True:
        print "***\t\t%s NEIGHBORS***" % (vendor)
        n = raw_input("\t\tNeighbor information (Press any key to continue. Press 'q' to quit): ")
        if n is not 'q':
            neighbor_id = raw_input("\t\tNeighbor ID (eg. x.x.x.x): ")
            neighbor_as = raw_input("\t\tNeighbor AS: ")
            if vendor == "cisco":
                cisco_neighbors[neighbor_id] = neighbor_as
                neighbors[vendor] = cisco_neighbors
            elif vendor == "juniper":
                juniper_neighbors[neighbor_id] = neighbor_as
                neighbors[vendor] = juniper_neighbors
            else:
                vyatta_neighbors[neighbor_id] = neighbor_as
                neighbors[vendor] = vyatta_neighbors
        else:
                break
    return neighbors

def read_file(filename):
    """ this function reads the node file and returns the content in a
    dictionary format.
    Arguments:
        <filename> string: the file name to read.

    Returns:
        <nodes> dictionary: contains the parsed content of <filename>
            example:
            nodes = {
                "router1": {"ipv4_address": "10.1.1.1", "platform": "CiscoIOS"},
            }
    """
    nodes = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                params = {}
                device_list = line.split()
                router = device_list[0]
                ip = device_list[1]
                platform = device_list[2]
                params["ipv4_address"] = ip
                params["platform"] = platform
                nodes[router] = params
    except IOError:
        print "File %s does not exist!" % filename
    return nodes

def configure():
    """This creates a nice and userfriendly command line."""
    parser = argparse.ArgumentParser(description="welcome to AutomateBGP!")
    parser.add_argument('-u', '--username', dest='username',
            help='username to login to nodes')
    parser.add_argument('-p', '--password', dest='password',
            help='password to login to nodes')
    parser.add_argument('-f', '--filename', dest='filename',
            help='text file containing the node data (expected format...)')
    return parser.parse_args()

def main(args):
    """ This is the main function. """
    # Getting the missing parameters, if any.
    if not args.username:
        args.username = raw_input("Please enter username: ")
    if not args.password:
        args.password = getpass("Please enter password: ")
    if not args.filename:
        args.filename = raw_input("Please enter filename: ")
    # Reading file.
    nodes = read_file(args.filename)
    # Open the vars file.
    vars_file = open("./roles/router/vars/main.yml", 'a')
    # Obtaining loopback information.
    neighbors = {"cisco" : "", "juniper" : "", "vyatta" : "" }
    cisco, cisco_as = CiscoLoopback()
    juniper, juniper_as = JuniperLoopback()
    vyatta, vyatta_as = VyattaLoopback()
    # Obtaining neighbors information.
    cisco_ne = Neighbors("cisco")
    juniper_ne = Neighbors("juniper")
    vyatta_ne = Neighbors("vyatta")
    # Starting to buil the file's schema.
    cisco_vars = CISCOTEMPLATE % (cisco_as)
    vars_file.write(cisco_vars)
    for interface in cisco:
        a = CISCOLOOPBACK % (interface, cisco[interface]["address"], cisco[interface]["network"], cisco[interface]["mask"])
        vars_file.write(a)

    vars_file.write(CISCONEIGHBORS)
    for neighbor in cisco_ne:
        if neighbor == "cisco":
            for element in cisco_ne[neighbor]:
                a = NEIGHBORS % (element, cisco_ne[neighbor][element])
                vars_file.write(a)

    juniper_vars = JUNIPERTEMPLATE % (juniper_as)
    vars_file.write(juniper_vars)
    for interface in juniper:
        a = LOOPBACK % (interface, juniper[interface]["address"], juniper[interface]["network"])
        vars_file.write(a)
    vars_file.write(JUNIPERNEIGHBORS)
    for neighbor in juniper_ne:
        if neighbor == "juniper":
            for element in juniper_ne[neighbor]:
                a = NEIGHBORS % (element, juniper_ne[neighbor][element])
                vars_file.write(a)

    vyatta_vars = VYATTATEMPLATE % (vyatta_as)
    vars_file.write(vyatta_vars)
    for interface in vyatta:
        a = LOOPBACK % (interface, vyatta[interface]["address"], vyatta[interface]["network"])
        vars_file.write(a)
    vyatta_neighbors_var = VYATTANEIGHBORS
    vars_file.write(vyatta_neighbors_var)
    for neighbor in vyatta_ne:
        if neighbor == "vyatta":
            for element in vyatta_ne[neighbor]:
                a = NEIGHBORS % (element, vyatta_ne[neighbor][element])
                vars_file.write(a)
    # Closing and saving the file.
    vars_file.close()

    time.sleep(2)
    # Generating the templates.
    os.system("ansible-playbook site.yml")
    time.sleep(2)
    # Loading cisco configuration.
    try:
        with open("cisco_template.txt", 'r') as f:
            cisco_template = f.read()
    except IOError:
        print "File cisco_template does not exist!"
    # Loading Juniper configuration.
    try:
        with open("juniper_template.txt", 'r') as f:
            juniper_template = f.read()
    except IOError:
        print "File juniper_template does not exist!"
    # Loading Vyatta configuration.
    try:
        with open("vyatta_template.txt", 'r') as f:
            vyatta_template = f.read()
    except IOError:
        print "File vyatta_template does not exist!"
    # Configuring the devices.
    for device in nodes:
        if nodes[device]["platform"] == "CiscoIOS":
            run_commands(nodes[device]["ipv4_address"], args.username, args.password, cisco_template, platform="cisco")
            print "***CISCO CONFIGURATION COMPLETED***"
        elif nodes[device]["platform"] == "Juniper":
            run_commands(nodes[device]["ipv4_address"], args.username, args.password, juniper_template, platform="juniper")
            print "***JUNIPER CONFIGURATION COMPLETED***"
        else:
            run_commands(nodes[device]["ipv4_address"], args.username, args.password, vyatta_template, platform="vyatta")
            print "***VYATTA CONFIGURATION COMPLETED***"

if __name__ == "__main__":
    sys.exit(main(configure()))
                                                              
