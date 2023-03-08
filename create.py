#!/usr/bin/python3
# Notes
# ask for amount
# clients, teamservers, rediretors, DCs, workstations, users
# make it so you can pick exactly what you want e.g.:
# ./create.py -c 1 -dc 1 -wk 5 -u 50
# Assume breach option -> give beacon -> gives random shell as a user on a Workstation

# FIX
# Issues when deploying just 1 machine and no DC in inventory as it can't set DNS, maybe ask for DC ip for when windows machine specified, this will be handy once checks in place


import ipaddress
import yaml
import random
from termcolor import colored

# Purely to hide that ugly CTRL+C output
import signal
import sys
signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))
# Purely to hide that ugly CTRL+C output

COLOURS = ["black","blue","cyan","dark_grey","green","light_blue","light_cyan","light_green","light_grey","light_magenta","light_red","light_yellow","magenta","red","white","yellow"]

DIVIDE = """
  .-.-.   .-.-.   .-.-.   .-.-.   .-.-.   .-.-.   .-.-.   .-.-
 / / \ \ / / \ \ / / \ \ / / \ \ / / \ \ / / \ \ / / \ \ / / \\
`-'   `-`-'   `-`-'   `-`-'   `-`-'   `-`-'   `-`-'   `-`-'"""

PTAH = [
  "                                                "
 ,"               ██████╗ ████████╗ █████╗ ██╗  ██╗"
 ,"               ██╔══██╗╚══██╔══╝██╔══██╗██║  ██║"
 ,"               ██████╔╝   ██║   ███████║███████║"
 ,"               ██╔═══╝    ██║   ██╔══██║██╔══██║"
 ,"               ██║        ██║   ██║  ██║██║  ██║"
 ,"               ╚═╝        ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝"]

MAIN = {"1":"Deploy", "2":"Assume Breach", "99":"Setup Help"}
BREACH = {""}
DIGITS = ["0","1","2","3","4","5","6","7","8","9"] # Sure theres a better way than this
INVENTORY = "inventory.yml"

LINUX = ["attacker", "teamserver", "redirector"]
WINDOWS = ["dc", "iis", "cert", "fileserver", "workstation"]

inventory = [
    ["attacker", "", ""],
    ["teamserver", "", ""],
    ["redirector", "", ""],
    ["dc", "", ""],
    ["iis", "", ""],
    ["cert","", ""],
    ["fileserver","", ""],
    ["workstation", "", ""],
]

inven_vars = {'ansible_user': 'ansible', 
              'ansible_password': 'Passw0rd!',
              'ansible_port': 5986,
              'ansible_connection': 'winrm',
              'ansible_winrm_transport': 'basic',
              'ansible_winrm_server_cert_validation': 'ignore',
              'ansible_winrm_operation_timeout_sec': 120,
              'ansible_winrm_read_timeout_sec': 130,
              'windows_gateway': '10.10.10.1',
              'windows_mask': '255.255.0.0',
              'ansible_become_user': '{{ NetBIOS}}\\administrator',
              'ansible_become_password': 'Passw0rd!'}

def splash():
    border_colour = random.choice(COLOURS)
    print(colored(DIVIDE, border_colour)) 
    for i in PTAH:
        print(colored(i, random.choice(COLOURS)))
    print(colored(DIVIDE, border_colour))

def get_input(possibles):
    cursor = "Choice -> "
    choice = ""

    while choice not in possibles:
        print(colored(cursor, 'magenta'), end = "")
        choice = input()
    return choice

def validate_ip_address(ip_string):
   try:
        ip_object = ipaddress.ip_address(ip_string)
        return True
   except ValueError:
        if ip_string == "": return False
        else:
            print(colored("Not a valid IP!", "red"))
            return False

def get_ips(amount):
    cursor = "IP -> "
    choice = "jim"
    ip = ""
    concat_ips = ""

    amount = int(amount)

    for i in range(amount):
        while not validate_ip_address(ip):
            print(colored(cursor, 'yellow'), end = "")
            ip = input()

        concat_ips = concat_ips + ip + "~"
        ip = ""

    return concat_ips[:-1]

def clear_inventory():
    # Open file for reading
    with open(f'{INVENTORY}','r') as f:
        output = yaml.safe_load(f)
    # Clear all IPs
    for host in LINUX:
        output["linux"]["children"][host]["hosts"] = None
    for host in WINDOWS:
        output["windows"]["children"][host]["hosts"] = None
    
    # Save new inventory
    with open(f'{INVENTORY}', 'w') as f:
        yaml.safe_dump(output,f , sort_keys=False)

def edit_inventory():
    global inven_vars

    windows_found = False
    clear_inventory()
    # Open file for reading
    with open(f'{INVENTORY}','r') as f:
        output = yaml.safe_load(f)
    
    for host in inventory:
        # Check for empty amount
        if host[1] == "": continue
        
        # Get variables from list
        # ['attacker', '2', '2.2.2.2~3.3.3.3.3']
        host_type = host[0]
        amount = int(host[1])
        ips = host[2].split("~")

        # I hope nobody ever reads this code....
        if(host_type in LINUX and host[1] != "0"):
            output["linux"]["children"][host_type]["hosts"] = {"temp":"temp"}
        if(host_type in WINDOWS and host[1] != "0"):
            output["windows"]["children"][host_type]["hosts"] = {"temp":"temp"}

        # For amount of addresses add to dict
        for a in range(amount):
            hostname = host_type + "{:02d}".format(a + 1)

            if(host_type in LINUX):
                output["linux"]["children"][host_type]["hosts"][hostname] = {'ansible_host': ips[a]}
                output["linux"]["children"][host_type]["hosts"].pop("temp", None)
            if(host_type in WINDOWS):
                windows_found = True
                output["windows"]["children"][host_type]["hosts"][hostname] = {'ansible_host': ips[a]}
                output["windows"]["children"][host_type]["hosts"].pop("temp", None)

  
    # Get gatway and subnet mask for Windows hosts
    if(windows_found):
        # Gateway
        print(colored("Windows Gateway IP: ", 'green'))
        choice = get_ips(1)
        temp = {"windows_gateway": choice}
        inven_vars.update(temp)

        # Subnet Mask
        print(colored("Windows Subnet Mask: ", 'green'))
        choice = get_ips(1)
        temp = {"windows_mask": choice}
        inven_vars.update(temp)

        # Add to output
        output["windows"]["vars"] = inven_vars
        
    # Save new inventory
    try:
        with open(f'{INVENTORY}', 'w') as f:
            yaml.safe_dump(output,f , sort_keys=False)
        print(colored("Inventory Saved!", 'blue'))
    except:
        print(colored("Inventory failed to save... oh noe", 'red'))

def deploy():
    for i in inventory:
        text = "Amount of " + i[0] + "'s: "

        print(colored(text, 'green'))
        choice = get_input(DIGITS)

        i[1] = choice
        i[2] = get_ips(i[1])

    edit_inventory()

def print_menu(menu):
    for key in menu:
        tab = key + ": "

        print(colored(tab, 'white'), end = "") # e.g. 1:
        print(colored(menu[key], 'blue'))

    choice = get_input(menu)
    return choice

if __name__ == "__main__":
    splash()
    choice = print_menu(MAIN)
    if(choice == "1"): deploy()