#!/usr/bin/python

# All SSH libraries for Python are junk (2011-10-13).
# Too low-level (libssh2), too buggy (paramiko), too complicated
# (both), too poor in features (no use of the agent, for instance)

# Here is the right solution today:
__doc__ = "ssh sample app"
import subprocess
import sys
import paramiko

def ssh_command(command):

    # A2 Hosting site
    IP="a2ss54.a2hosting.com"
    PORT=7822
    USER="southme1"
    PWD ="Python7713,./"

    """
    # bplaced.net  - ssh not supported
    IP="144.76.167.69"  #"www.kaiserware.bplace.net"
    PORT=7822
    USER="kaiserware"
    PWD ="vesret2204"
    """

    client = paramiko.client.SSHClient()
    #client.load_host_keys('file name with SSK key authentication')
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(IP, port=PORT, username=USER, password=PWD, look_for_keys=False)
    ssh_session = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.exec_command(command)
        print ("\nConnected to SSH shell at host %s and executed command %s\n" %(IP, command))
        str = ssh_session.recv(1024).decode("utf-8")
        print(str)
    else:
        print ("\nCould'nt connect to the SSH session at %s\n" %IP)

    return
"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print (__doc__)
    ssh_command("ls -l")
