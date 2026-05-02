#!/usr/bin/python3

import ipaddress
import re
import string
import validators
import yaml
import random
import subprocess
import urllib.request
from termcolor import colored

import signal
import sys
signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))

COLOURS = ["black","blue","cyan","dark_grey","green","light_blue","light_cyan","light_green",
           "light_grey","light_magenta","light_red","light_yellow","magenta","red","white","yellow"]

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

MAIN  = {"1": "Deploy", "2": "Assume Breach", "99": "Setup Help"}
TYPES = {"1": "EXE", "2": "PS1"}
YESNO = {"1": "Yes", "2": "No"}

BREACH_FACTS = "roles/windows/breach/defaults/main.yml"
BREACH_TASKS = "breach.yml"
BREACH_CMD   = "ansible-playbook -i inventory.yml breach.yml"

INVENTORY = "inventory.yml"
AD_VARS   = "group_vars/windows/active_directory.yml"
LINUX     = ["attacker", "teamserver", "redirector"]
WINDOWS   = ["dc", "exchange", "iis", "cert", "fileserver", "workstation"]

EX2016 = "roles/windows/servers/exchange/files/exchangeserver2016.iso"

DOMAIN_RE = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
)

inventory = [
    ["attacker",   "", ""],
    ["teamserver", "", ""],
    ["redirector", "", ""],
    ["dc",         "", ""],
    ["exchange",   "", ""],
    ["iis",        "", ""],
    ["cert",       "", ""],
    ["fileserver", "", ""],
    ["workstation","", ""],
]

inven_vars = {
    'ansible_user':                          'ansible',
    'ansible_password':                      'Passw0rd!',
    'ansible_port':                          5986,
    'ansible_connection':                    'winrm',
    'ansible_winrm_transport':               'basic',
    'ansible_winrm_server_cert_validation':  'ignore',
    'ansible_winrm_operation_timeout_sec':   120,
    'ansible_winrm_read_timeout_sec':        130,
    'windows_gateway':                       '10.10.10.1',
    'windows_mask':                          '255.255.0.0',
    'ansible_become_password':               'Passw0rd!',
}


def splash():
    border_colour = random.choice(COLOURS)
    print(colored(DIVIDE, border_colour))
    for line in PTAH:
        print(colored(line, random.choice(COLOURS)))
    print(colored(DIVIDE, border_colour))


def get_input(possibles):
    choice = ""
    while choice not in possibles:
        print(colored("Choice -> ", 'magenta'), end="")
        choice = input()
    return choice


def validate_ip(ip_string):
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        if ip_string:
            print(colored("Not a valid IP!", "red"))
        return False


def validate_url(url):
    if not validators.url(url):
        print(colored("Not a valid URL!", "red"))
        return False
    return True


def validate_domain(domain):
    if DOMAIN_RE.match(domain):
        return True
    print(colored("Not a valid domain! (e.g. corp.local)", "red"))
    return False


def get_ips(amount):
    ips = []
    for _ in range(int(amount)):
        ip = ""
        while not validate_ip(ip):
            print(colored("IP -> ", 'yellow'), end="")
            ip = input()
        ips.append(ip)
    return "~".join(ips)


def get_url():
    url = ""
    while not validate_url(url):
        print(colored("URL -> ", 'yellow'), end="")
        url = input()
    return url


def get_domain():
    domain = ""
    while not validate_domain(domain):
        print(colored("Domain -> ", 'yellow'), end="")
        domain = input()
    return domain


def update_domain(domain):
    with open(AD_VARS, 'r') as f:
        content = f.read()
    content = re.sub(r'^Domain:.*$', f'Domain: {domain}', content, flags=re.MULTILINE)
    with open(AD_VARS, 'w') as f:
        f.write(content)
    print(colored(f"Domain set to: {domain}", 'blue'))


def get_exchange():
    try:
        open(EX2016, 'r').close()
        print(colored("Exchange 2016 ISO found, SMASHING!", 'blue'))
    except IOError:
        print(colored("Exchange 2016 ISO not found, BOGUS!", 'red'))
        print(colored("Wish to download Exchange 2016 ISO:", 'green'))
        if print_menu(YESNO) == "1":
            print(colored("Downloading ~5.6GiB Please Wait!... ", 'blue'))
            urllib.request.urlretrieve(
                'https://download.microsoft.com/download/2/5/8/258D30CF-CA4C-433A-A618-FB7E6BCC4EEE/ExchangeServer2016-x64-cu12.iso',
                EX2016
            )
            print(colored("Download Complete :)", 'blue'))
        else:
            print(colored("Come back when you've got the ISO buddy!", 'red'))


def clear_inventory():
    with open(INVENTORY, 'r') as f:
        output = yaml.safe_load(f)
    for host in LINUX:
        output["linux"]["children"][host]["hosts"] = None
    for host in WINDOWS:
        output["windows"]["children"][host]["hosts"] = None
    with open(INVENTORY, 'w') as f:
        yaml.safe_dump(output, f, sort_keys=False)


def edit_inventory():
    global inven_vars

    windows_found = False
    clear_inventory()

    with open(INVENTORY, 'r') as f:
        output = yaml.safe_load(f)

    for host in inventory:
        if host[1] == "" or host[1] == "0":
            continue

        host_type = host[0]
        amount    = int(host[1])
        ips       = host[2].split("~")

        if host_type in LINUX:
            output["linux"]["children"][host_type]["hosts"] = {}
        if host_type in WINDOWS:
            output["windows"]["children"][host_type]["hosts"] = {}
            windows_found = True

        for a in range(amount):
            hostname = host_type + "{:02d}".format(a + 1)
            ip_entry = {'ansible_host': ips[a]}
            if host_type in LINUX:
                output["linux"]["children"][host_type]["hosts"][hostname] = ip_entry
            if host_type in WINDOWS:
                output["windows"]["children"][host_type]["hosts"][hostname] = ip_entry

    if windows_found:
        print(colored("Windows Gateway IP: ", 'green'))
        inven_vars["windows_gateway"] = get_ips(1)
        print(colored("Windows Subnet Mask: ", 'green'))
        inven_vars["windows_mask"] = get_ips(1)
        output["windows"]["vars"] = inven_vars

    try:
        with open(INVENTORY, 'w') as f:
            yaml.safe_dump(output, f, sort_keys=False)
        print(colored("Inventory Saved!", 'blue'))
        print(colored("Please Run: ", 'blue'), end='')
        print(colored("ansible-playbook -i inventory.yml deploy.yml", 'green'))
    except Exception as e:
        print(colored(f"Inventory failed to save: {e}", 'red'))


def deploy():
    for i in inventory:
        print(colored(f"Amount of {i[0]}'s: ", 'green'))
        i[1] = get_input(string.digits)
        i[2] = get_ips(i[1])
        if i[0] == "exchange":
            get_exchange()

    windows_selected = any(i[0] in WINDOWS and i[1] not in ("", "0") for i in inventory)
    if windows_selected:
        print(colored("Active Directory Domain (e.g. corp.local): ", 'green'))
        update_domain(get_domain())

    edit_inventory()


def breach():
    with open(BREACH_FACTS, 'r') as f:
        output = yaml.safe_load(f)

    print(colored("Please supply beacon url:", 'green'))
    output['beacon_url'] = get_url()

    print(colored("Please supply beacon type:", 'green'))
    output['beacon_type'] = TYPES[print_menu(TYPES)]

    with open(INVENTORY, 'r') as f:
        inven = yaml.safe_load(f)

    work_hosts = inven["windows"]["children"]["workstation"]["hosts"]
    rand_workstation = random.choice(list(work_hosts.keys()))

    with open(BREACH_TASKS, 'r') as f:
        tasks = yaml.safe_load(f)
    tasks[0]["hosts"] = rand_workstation
    with open(BREACH_TASKS, 'w') as f:
        yaml.safe_dump(tasks, f, sort_keys=False)

    with open(BREACH_FACTS, 'w') as f:
        yaml.safe_dump(output, f, sort_keys=False)

    print(colored("Ready for a beacon?:", 'red'))
    if print_menu(YESNO) == "1":
        print(colored(f"Attacking: {rand_workstation}\nPLEASE WAIT.....", 'red'))
        process = subprocess.Popen(BREACH_CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
    else:
        print(colored("ok bye!", 'blue'))


def print_menu(menu):
    for key, label in menu.items():
        print(colored(f"{key}: ", 'white'), end="")
        print(colored(label, 'blue'))
    return get_input(menu)


if __name__ == "__main__":
    splash()
    choice = print_menu(MAIN)
    if choice == "1": deploy()
    if choice == "2": breach()
