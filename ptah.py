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

MAIN  = {"1": "Deploy", "2": "Assume Breach", "3": "View Lab"}
TYPES = {"1": "EXE", "2": "PS1"}
YESNO = {"1": "Yes", "2": "No"}

BREACH_FACTS = "roles/windows/breach/defaults/main.yml"
BREACH_TASKS = "breach.yml"
BREACH_CMD   = "ansible-playbook -i inventory.yml breach.yml"

INVENTORY = "inventory.yml"
AD_VARS   = "group_vars/windows/active_directory.yml"
LINUX     = ["attacker", "teamserver", "redirector"]
WINDOWS   = ["dc", "exchange", "iis", "cert", "fileserver", "workstation"]
DOMAIN_SERVERS = ["exchange", "iis", "cert", "fileserver", "workstation"]

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
    if domain:
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


def print_summary(domain):
    active = [i for i in inventory if i[1] not in ("", "0")]
    if not active:
        print(colored("  No hosts configured.", 'red'))
        return

    print(colored(DIVIDE, 'cyan'))
    print(colored("  DEPLOYMENT SUMMARY", 'white'))
    print(colored(DIVIDE, 'cyan'))

    for i in active:
        ips = i[2].split("~") if i[2] else []
        ip_str = ", ".join(ips)
        label = colored(f"  {i[0]:<14}", 'white')
        count = colored(f"x{i[1]:<4}", 'yellow')
        print(f"{label} {count} {colored(ip_str, 'green')}")

    if domain:
        print()
        print(colored(f"  Domain:   {domain}", 'cyan'))
        print(colored(f"  Gateway:  {inven_vars['windows_gateway']}", 'cyan'))
        print(colored(f"  Mask:     {inven_vars['windows_mask']}", 'cyan'))

    print(colored(DIVIDE, 'cyan'))


def clear_inventory():
    with open(INVENTORY, 'r') as f:
        output = yaml.safe_load(f)
    for host in LINUX:
        output["linux"]["children"][host]["hosts"] = None
    for host in WINDOWS:
        output["windows"]["children"][host]["hosts"] = None
    with open(INVENTORY, 'w') as f:
        yaml.safe_dump(output, f, sort_keys=False)


def edit_inventory(windows_found):
    clear_inventory()

    with open(INVENTORY, 'r') as f:
        output = yaml.safe_load(f)

    for host in inventory:
        if host[1] in ("", "0"):
            continue

        host_type = host[0]
        amount    = int(host[1])
        ips       = host[2].split("~")

        if host_type in LINUX:
            output["linux"]["children"][host_type]["hosts"] = {}
        if host_type in WINDOWS:
            output["windows"]["children"][host_type]["hosts"] = {}

        for a in range(amount):
            hostname  = host_type + "{:02d}".format(a + 1)
            ip_entry  = {'ansible_host': ips[a]}
            if host_type in LINUX:
                output["linux"]["children"][host_type]["hosts"][hostname] = ip_entry
            if host_type in WINDOWS:
                output["windows"]["children"][host_type]["hosts"][hostname] = ip_entry

    if windows_found:
        output["windows"]["vars"] = inven_vars

    try:
        with open(INVENTORY, 'w') as f:
            yaml.safe_dump(output, f, sort_keys=False)
        print(colored("Inventory Saved!", 'blue'))
    except Exception as e:
        print(colored(f"Inventory failed to save: {e}", 'red'))
        return

    deploy_cmd = "ansible-playbook -i inventory.yml deploy.yml"
    print(colored(f"Run: {deploy_cmd}", 'green'))
    print(colored("Execute now?", 'green'))
    if print_menu(YESNO) == "1":
        print(colored("Deploying lab, please wait...", 'blue'))
        subprocess.run(deploy_cmd.split())


def deploy():
    for i in inventory:
        print(colored(f"Amount of {i[0]}'s: ", 'green'))
        i[1] = get_input(list(string.digits))
        i[2] = get_ips(i[1])
        if i[0] == "exchange":
            get_exchange()

    windows_selected = any(i[0] in WINDOWS and i[1] not in ("", "0") for i in inventory)

    domain = None
    if windows_selected:
        dc_count = next((int(i[1]) for i in inventory if i[0] == "dc"), 0)
        needs_dc = [i[0] for i in inventory if i[0] in DOMAIN_SERVERS and i[1] not in ("", "0")]
        if dc_count == 0 and needs_dc:
            print(colored(f"  WARNING: {', '.join(needs_dc)} configured but no DC — these hosts won't join a domain!", 'red'))

        print(colored("Active Directory Domain (e.g. corp.local): ", 'green'))
        domain = get_domain()

        print(colored("Windows Gateway IP: ", 'green'))
        inven_vars["windows_gateway"] = get_ips(1)
        print(colored("Windows Subnet Mask: ", 'green'))
        inven_vars["windows_mask"] = get_ips(1)

    print_summary(domain)
    print(colored("Proceed with deployment?", 'green'))
    if print_menu(YESNO) != "1":
        print(colored("Aborted.", 'red'))
        return

    if domain:
        update_domain(domain)
    edit_inventory(windows_selected)


def view_inventory():
    with open(INVENTORY, 'r') as f:
        inven = yaml.safe_load(f)

    print(colored(DIVIDE, 'cyan'))
    print(colored("  CURRENT LAB", 'white'))
    print(colored(DIVIDE, 'cyan'))

    found_any = False

    for group, hosts_key, colour in [("linux", LINUX, 'green'), ("windows", WINDOWS, 'cyan')]:
        for host in hosts_key:
            hosts = (inven.get(group, {})
                         .get("children", {})
                         .get(host, {})
                         .get("hosts")) or {}
            for hostname, data in hosts.items():
                ip = data.get('ansible_host', '') if isinstance(data, dict) else ''
                print(colored(f"  {hostname:<16} {ip}", colour))
                found_any = True

    if not found_any:
        print(colored("  No hosts configured.", 'red'))
    else:
        try:
            with open(AD_VARS, 'r') as f:
                ad = yaml.safe_load(f)
            print()
            print(colored(f"  Domain:  {ad.get('Domain', '')}", 'yellow'))
            win_vars = inven.get("windows", {}).get("vars", {})
            if win_vars:
                print(colored(f"  Gateway: {win_vars.get('windows_gateway', '')}", 'yellow'))
                print(colored(f"  Mask:    {win_vars.get('windows_mask', '')}", 'yellow'))
        except Exception:
            pass

    print(colored(DIVIDE, 'cyan'))


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
    if choice == "3": view_inventory()
