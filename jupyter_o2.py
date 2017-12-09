#!/usr/bin/env python

#
# A script to launch and connect to a Jupyter session on Orchestra 2,
# an HPC cluster managed by the HMS Resesarch Computing group.
#
# Usage: jupyter_o2 <USER> <subcommand>

# Example: jupyter_o2 js123 notebook
# This will launch an X11-enabled ssh, start an interactive node running jupyter notebook,
# ssh into that interactive node to allow requests to be forwarded,
# and finally open the notebook in your browser.
#
# If jupyter hangs when opening notebooks for the first time in any session,
# and the console shows a "The signatures database cannot be opened" error,
# enter an interactive session and generate a notebook config using
#   `jupyter notebook --generate-config`
# then set c.NotebookNotary.db_file = ':memory:'
#

from __future__ import print_function
import sys
import os
import argparse
import getpass  # fallback if pinentry is not installed ("brew install pinentry" on macs)
import subprocess
import re
from pexpect import pxssh
import webbrowser
import ctypes
import atexit
from signal import signal, SIGABRT, SIGINT, SIGTERM
try:
    # optional import of dnspython to resolve "Unknown host" errors
    # if you get errors like "Could not establish connection to host",
    # test the server with nslookup <host>
    # your current DNS server may not have entries for the individual O2 login nodes
    import dns.resolver
except ModuleNotFoundError:
    dns = None

#####################################################
# variables to set                                  #
# choose a jp_port that is open on your machine     #
#####################################################

HOST = "o2.hms.harvard.edu"
DEFAULT_JP_PORT = 8887  # pick an open port on your machine
DEFAULT_JP_TIME = "0-3:00"  # 3 hours
DEFAULT_JP_MEM = "1G"
DEFAULT_JP_CORES = 1
SOURCE_JUPYTER_CALL = "py35"  # the bash command to enter your jupyter environment (one line, use semicolons if needed)

parser = argparse.ArgumentParser(description='Launch and connect to a Jupyter session on O2.')
parser.add_argument("user", type=str, help="O2 username")
parser.add_argument("subcommand", help="the subcommand to launch")
parser.add_argument("-p", "--port", type=int, default=DEFAULT_JP_PORT, help="Available port on your system")
parser.add_argument("-t", "--time", type=str, default=DEFAULT_JP_TIME, help="Time to run Jupyter")
parser.add_argument("-m", "--mem", type=str, default=DEFAULT_JP_MEM, help="Memory to allocate for Jupyter")
parser.add_argument("-c", "-n", dest="cores", type=int, default=DEFAULT_JP_CORES, help="Cores to allocate for Jupyter")
parser.add_argument("-k", "--keepalive",  default=False, action='store_true', help="Keep interactive session alive after exiting Jupyter")
args = parser.parse_args(sys.argv[1:])

user = args.user
host = HOST
jp_port = args.port

srun_call = "srun -t {} --mem {} -n {} --pty -p interactive --x11 /bin/bash".format(args.time, args.mem, args.cores)
jp_call = "jupyter {} --port={} --browser='none'".format(args.subcommand, jp_port)

if sys.platform.startswith("linux"):
    my_pinentry_path = "/usr/bin/pinentry"
elif sys.platform == "darwin":
    my_pinentry_path = "/usr/local/bin/pinentry"
else:
    my_pinentry_path = "pinentry"

if dns is not None:
    my_resolver = dns.resolver.Resolver()
else:
    my_resolver = None

dns_server_groups = [  # dns servers that have entries for loginXX.o2.rc.hms.harvard.edu
    my_resolver.nameservers,                                # current nameservers, checked first
    ["134.174.17.6", "134.174.141.2"],                      # HMS nameservers
    ["128.103.1.1", "128.103.201.100", "128.103.200.101"]   # HU nameservers
]
# test that you can access the login nodes with nslookup login01.o2.rc.hms.harvard.edu <DNS>


#####################################################
# functions and classes                             #
#####################################################


def check_dns(hostname):
    dns_err_code = 0
    if dns is not None:
        for dns_servers in dns_server_groups:
            try:
                my_resolver.nameservers = dns_servers
                if dns_err_code > 0:
                    print("Could not resolve domain. Trying with nameservers: {}".format(dns_servers))
                    answer = my_resolver.query(hostname)
                    hostname = answer[0].address
                    dns_err_code = 1
                else:
                    my_resolver.query(hostname)
                break
            except dns.resolver.NXDOMAIN:
                dns_err_code = 2
    if dns_err_code == 1:
        print("Found IP: {}".format(jp_login_host))
    elif dns_err_code == 2:
        print("No IP found for {}".format(jp_login_host))
    return dns_err_code, hostname


class FilteredOut(object):
    def __init__(self, txtctrl, by):
        self.txtctrl = txtctrl
        self.by = by

    def write(self, bytestr):
        try:
            if bytestr[:len(self.by)] == self.by:
                self.txtctrl.write(bytestr)
        except IndexError:
            pass

    def flush(self):
        self.txtctrl.flush()

    def exit_on_find(self, bytestr):
        if self.by in bytestr:
            sys.exit(0)
        return bytestr


def clean(*_):
    print("Cleaning up\r")
    if "o2_pass" in globals():
        zero(o2_pass)
    if "login_ssh" in globals():
        if not login_ssh.closed:
            print("Closing login_ssh")
        login_ssh.close(force=True)
    if "second_ssh" in globals():
        if not second_ssh.closed:
            print("Closing second_ssh")
        login_ssh.close(force=True)
    os._exit(0)


# perform clean() on exit or interrupt
atexit.register(clean)
for sig in (SIGABRT, SIGINT, SIGTERM):
    signal(sig, clean)


#####################################################################
# first import pin entry and security functions from pysectools,    #
# updated version of pysectools for python 3:                       #
#   uses bytestrings and flushes stdin after writing                #
#   slightly modified from Greg V:                                  #
#                                                                   #
# Copyright © 2013-2015 Greg V <greg@unrelenting.technology>        #
# This work is free. You can redistribute it and/or modify it       #
# under the terms of the                                            #
# Do What The Fuck You Want To Public License, Version 2,           #
# as published by Sam Hocevar.                                      #
#                                                                   #
#####################################################################


def zero(s):
    """
    Tries to securely erase a secret string from memory
    (overwrite it with zeros.)

    Only works on CPython.

    Returns True if successful, False otherwise.
    """
    try:
        bufsize = len(s) + 1
        offset = sys.getsizeof(s) - bufsize
        location = id(s) + offset
        ctypes.memset(location, 0, bufsize)
        return True
    except:
        return False


def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0


class PinentryException(Exception):
    pass


class PinentryUnavailableException(PinentryException):
    pass


class PinentryClosedException(PinentryException):
    pass


class Pinentry(object):
    def __init__(self, pinentry_path="pinentry", fallback_to_getpass=True):
        if cmd_exists(pinentry_path):
            if fallback_to_getpass and os.isatty(sys.stdout.fileno()):
                self._ask = self._ask_with_getpass
                self._close = self._close_getpass
            else:
                raise PinentryUnavailableException()
        else:
            self.process = subprocess.Popen(pinentry_path,
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT,
                                            close_fds=True)
            self._ask = self._ask_with_pinentry
            self._close = self._close_pinentry
        self._closed = False

    def ask(self,
            prompt="Enter the password: ",
            description=None,
            error="Wrong password!",
            validator=lambda x: x is not None):
        if self._closed:
            raise PinentryClosedException()
        return self._ask(prompt, description, error, validator)

    def close(self):
        self._closed = True
        return self._close()

    @staticmethod
    def _ask_with_getpass(prompt, description, error, validator):
        if description:
            print(description)
        password = None
        while not validator(password):
            if password is not None:
                print(error)
            password = getpass.getpass(prompt)
        return password

    def _close_getpass(self): pass

    def _ask_with_pinentry(self, prompt, description, error, validator):
        self._waitfor("OK")
        env = os.environ.get
        self._comm("OPTION lc-ctype=%s" % env("LC_CTYPE", env("LC_ALL", "en_US.UTF-8")))
        try:
            self._comm("OPTION ttyname=%s" % env("TTY", os.ttyname(sys.stdout.fileno())))
        except:
            pass
        if env('TERM'):
            self._comm("OPTION ttytype=%s" % env("TERM"))
        if prompt:
            self._comm("SETPROMPT %s" % self._esc(prompt))
        if description:
            self._comm("SETDESC %s" % self._esc(description))
        password = None
        while not validator(password):
            if password is not None:
                self._comm("SETERROR %s" % self._esc(error))
            self.process.stdin.write(b"GETPIN\n")
            self.process.stdin.flush()
            password = self._waitfor("D ", breakat="OK")
            if password is not None:
                password = password[2:].replace("\n", "")
        return password

    def _close_pinentry(self):
        return self.process.kill()

    def _waitfor(self, what, breakat=None):
        out = ""
        while not out.startswith(what):
            if breakat is not None and out.startswith(breakat):
                break
            out = self.process.stdout.readline().decode('utf-8')
        return out

    def _comm(self, x):
        self.process.stdin.write(x.encode('utf-8') + b"\n")
        self.process.stdin.flush()
        self._waitfor("OK")

    @staticmethod
    def _esc(x):
        return x.replace("%", "%25").replace("\n", "%0A")


###################################################################
#   Now run SSH                                                   #
#   First SSH into an interactive node and run jupyter notebook   #
#   Then SSH into that node to set up forwarding                  #
#   Finally, open the jupyter notebook page in the browser.       #
###################################################################

pinentry = Pinentry(pinentry_path=my_pinentry_path, fallback_to_getpass=True)
o2_pass = pinentry.ask(prompt="Enter your passphrase: ",
                       description="Connect to O2 server for jupyter {}".format(args.subcommand),
                       error="No password entered", validator=lambda x: x is not None and len(x) > 0)
pinentry.close()

# start login ssh
print("ssh {}@{}".format(user, host))
# check that the host can be found
dns_err, host = check_dns(host)
if dns_err == 1:
    print("ssh {}@{}".format(user, host))
elif dns_err == 2:
    exit(1)
login_ssh = pxssh.pxssh(timeout=60, ignore_sighup=False, options={
    "ForwardX11": "yes",
    "LocalForward": "{} 127.0.0.1:{}".format(jp_port, jp_port),
    "PubkeyAuthentication": "no"})
login_ssh.force_password = True
login_ssh.logfile = None  # prevent password from being printed into a logfile
login_ssh.logfile_send = None
login_ssh.logfile_read = None
login_ssh.login(host, user, o2_pass)

# get hostname
login_ssh.sendline("echo $HOSTNAME")
login_ssh.prompt()
jp_login_host = login_ssh.before.decode('utf-8').strip().split('\n')[1]
print("hostname: {}".format(jp_login_host))

# enter interactive
print()
# print("\nsrun -t 0-3:00 --pty -p interactive --x11 /bin/bash")
pass_pat = re.compile(b"[\w-]+@[\w-]+'s password: ")  # e.g. "user@compute-e-16-175's password: "
login_ssh.PROMPT = pass_pat
login_ssh.logfile_read = FilteredOut(sys.stdout.buffer, b'srun')
login_ssh.sendline(srun_call)
if not login_ssh.prompt():
    print("the timeout was reached.")
    exit(1)
login_ssh.logfile = None  # prevent password from being printed into a logfile
login_ssh.logfile_send = None
login_ssh.logfile_read = None
login_ssh.write(o2_pass.encode('utf-8') + b"\n")

# commands for within interactive: get hostname
login_ssh.PROMPT = login_ssh.UNIQUE_PROMPT
login_ssh.sendline("unset PROMPT_COMMAND; PS1='[PEXPECT]\$ '")
login_ssh.prompt()
login_ssh.sendline("hostname | sed 's/\..*//'")
login_ssh.prompt()
jp_interactive_host = login_ssh.before.decode('utf-8').strip().split('\n')[1]
print("interactive host: {}\n".format(jp_interactive_host))

# start jupyter
# print("\njupyter notebook --port={} --browser='none'".format(jp_port))
login_ssh.sendline(SOURCE_JUPYTER_CALL)
login_ssh.prompt()
login_ssh.sendline(jp_call)
login_ssh.logfile_read = sys.stdout.buffer
site_pat = re.compile("\W(https?://localhost:{}/\?token=\w+)\W".format(jp_port).encode('utf-8'))
login_ssh.PROMPT = site_pat
login_ssh.prompt()
jp_site = login_ssh.after.decode('utf-8').strip()

# log in to the second ssh
print("\nssh {}@{}".format(user, jp_login_host))
dns_err, jp_login_host = check_dns(jp_login_host)
if dns_err == 1:
    print("ssh {}@{}".format(user, jp_login_host))
elif dns_err == 2:
    exit(1)
second_ssh = pxssh.pxssh(timeout=10, ignore_sighup=False, options={"PubkeyAuthentication": "no"})
second_ssh.force_password = True
second_ssh.logfile = None  # prevent password from being printed into a logfile
second_ssh.logfile_send = None
second_ssh.logfile_read = None
second_ssh.login(jp_login_host, user, o2_pass)
# second_ssh.logfile_read = sys.stdout.buffer
while second_ssh.prompt(0.1):  # digest all prompts
    pass

# ssh into the running interactive node
print("\nssh -N -L {0}:127.0.0.1:{0} {1}".format(jp_port, jp_interactive_host))
second_ssh.PROMPT = pass_pat
second_ssh.sendline("ssh -N -L {0}:127.0.0.1:{0} {1}".format(jp_port, jp_interactive_host))
if not second_ssh.prompt():
    print("the timeout was reached.")
    exit(1)
second_ssh.logfile = None  # prevent password from being printed into a logfile
second_ssh.logfile_send = None
second_ssh.logfile_read = None
second_ssh.write(o2_pass.encode('utf-8') + b"\n")
zero(o2_pass)  # password is not needed anymore
second_ssh.logfile_read = sys.stdout.buffer

print("\nJupyter is ready! Access at:\n{}\nOpening in browser...".format(jp_site))
webbrowser.open(jp_site, new=2)

login_ssh.logfile = None
login_ssh.logfile_read = None
login_ssh.logfile_send = None
if args.keepalive:
    interact_filter = FilteredOut(None, b'[PEXPECT]$ logout')  # exits when you log out of the login shell
    login_ssh.interact(output_filter=interact_filter.exit_on_find)
else:
    interact_filter = FilteredOut(None, b'[PEXPECT]$ ')
    login_ssh.interact(output_filter=interact_filter.exit_on_find)  # exits when jupyter exits and [PEXPECT]$ appears
