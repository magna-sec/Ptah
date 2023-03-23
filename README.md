# Ptah
<p align="center" title="Hi">  <img src="images/logo.png" /> </p>

# ! WORK IN PROGRESS !
## Purpose:
I got bored of constantly installing/reinstalling tooling, redirectors, teamservers and AD networks. `Ptah` aims to create any attacking infra you need and the ability to create a randomly misconfigured AD lab.

`Ptah` is a "wrapper" around ansible, the script changes various facts (variables) in different files.

## Script:
- Features:
    - Alter your `inventory.yml`
    - Create a breach, providing you with a beacon as a random user.

This is a very rough script and very much a work in progress.

---
# Current Abilities
## Linux:
- Fill Ubuntu with decent tooling
- Deploy Teamservers for CS/PoshC2/Sliver
- Deploy Apache redirector
- Deploys with Scarecrow,Freeze,Donut,Ivy (more to add!)

## Windows:
The Windows Active Directory enviroment deploys randomly selected misconfigurations. This leads to interesting attack paths, for example:

**Bob member of GroupA -> GroupA has control over groupB -> GroupB is part of the DAs.**

Though of course this is totally randomly, so the possibilties are huge.

`Ptah` is also able to supply the attacker with a beacon from a random workstation. This is to simulate a random member of staff being phished.

Can currently deploy:
- Windows Active Directory (DC)
- Exchange 2016
- IIS
- ADCS - With ESC1 vulnerable certificate template
- Fileserver
- Windows 10 
- Active Directory misconfigurations (random)
- 1x Misconfig for each:
    - Group
    - User
    - Computer
    - Computer locally

---
## To Do:
- Machines:
    - PowerDNS... maybe?
    - Certbot for SSL
- Features:
    - Auto domain name -> redirector
    - Deploy logging/siem tools for blueteam esc stuff
    - Future future add the ability to make a network behind a router/firewall
    - Implement hardening options: e.g. "Do u want Applocker" etc
    - Make more vulnerable certs
    - Finish off misconfigs
    - Log random users in to create creds
    - Create domain trusts
    - Install Office.. somehow
    - Password Filter DLL Installed for local priv esc
    - Instead of installing AD etc, wipe current misconfigs/users and re-do, saves building etc.

- Tidying:
    - Optimise AD deployment .e.g not loop users 3? times
    - Change some of the PowerShell stuff to ansible (even though i tried that...)
    - Speed up adding users/groups etc






