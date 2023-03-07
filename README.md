# C2 Ansible
<p align="center" title="Hi">  <img src="images/logo.png" /> </p>

# ! WORK IN PROGRESS !
## Purpose:
I got bored of constantly installing/reinstalling tooling, redirectors, teamservers and AD networks. The dream would be to spin up around 3 Ubuntu machines, a few Windows machines and then let ansible do its thing and bam! A lab!

## Script:
A script is included `create.py` to help you create your `inventory.yml` files for deployment. This is a very rough script and very much a work in progress.


## Current Abilities
## Linux:
- Fill Ubuntu with decent tooling
- Deploy Teamservers for CS/PoshC2/Sliver
- Deploy Apache redirector
- Deploys with Scarecrow,Freeze,Donut,Ivy (more to add!)

## Windows:
The Windows Active Directory enviroment deploys randomly selected misconfigurations. This leads to interesting attack paths, for example:
User member of GroupA -> GroupA has control over groupB -> GroupB is part of the DAs.

Though of course this is totally randomly, so the possibilties are huge.

Can currently deploy:
- Windows Active Directory
- Active Directory misconfigs (random)
- Windows 10 
- IIS
- ADCS - With ESC1 vulnerable certificate template
- Fileserver
- 1x Misconfig for each:
    - Group
    - User
    - Computer
    - Computer locally

## To Do:
- Make more vulnerable certs
- Implement checks for most tasks in the main.ymls?
- Finish off misconfigs
- Speed up adding users/groups etc with forks.. I think?
- PowerDNS... maybe?
- Certbot for SSL
- Auto domain name -> redirector
- Optimise AD deployment .e.g not loop users 3? times
- Future future add the ability to make a network behind a router/firewall
- Add assume breach where you get a shell/beacon as a random user on a box
- Implement hardening options: e.g. "Do u want Applocker" etc
- Change some of the PowerShell stuff to ansible (even though i tried that...)
