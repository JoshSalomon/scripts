#!/usr/bin/python3

from main import run_main
import sys, getopt
import config
import logging

config = config.Config()


def usage():
    print(f'Usage: {sys.argv[0]} [OPTIONS]')
    print('Options:')
    print('-t | --threads <num>:  Number of concurrent threads in this test')
    print('                       Default %d' % config.threads)
    print('-c | --cycles <num>:   Number of cycles over the entire registry each thread performs')
    print('                       Default %d' % config.cycles)
    print('--quay-ip <ipaddress>: IP address of the Quay server')
    print('                       Default %s' % config.quay_ip)
    print('--quay-port <num>:     The port on which Quay server listens')
    print('                       Default is none')
    print('--use_https:           Use HTTPS protocol to connect to quay instead of http')
    print('                       Default %s' % config.verbose)
    print('-v | --verbose:        Print more info to the console')
    print('                       Default is %s' % config.verbose)
    print('--username <string>:   The username for logging into Quay')
    print('                       Default is %s' % config.username)
    print('--password <string>:   Password for the login')
    print('--print-config:        Print configuration before starting')
    print('-h | --help:           Print this message, and exit')


short_opts = "t:c:vh"
long_opts=[]
long_opts.append("threads=")
long_opts.append("cycles=")
long_opts.append("quay-ip=")
long_opts.append("quay-port=")
long_opts.append("use_https")
long_opts.append("verbose")
long_opts.append("username=")
long_opts.append("password=")
long_opts.append("print-config")
long_opts.append("help")

try:
    opts, args = getopt.getopt(sys.argv[1:], short_opts, long_opts)
except getopt.GetoptError:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)-8s] %(message)s',)
    logging.error("Error parsing command line arguments, exiting")
    usage()
    sys.exit(2)

#
# First thing find -h and print usage with the default values
#
for opt, _ in opts:
    if opt in ('-h', '--help'):
        usage()
        sys.exit()

print_config = False

for opt, arg in opts:
    if opt in ("-t", "--threads"):
        config.set_threads(int(arg))
    elif opt in ("-c", "--cycles"):
        config.set_cycles(int(arg))
    elif opt == "--quay-ip":
        config.set_quay_ip(arg)
    elif opt == "--quay-port":
        config.set_quay_port(int(arg))
    elif opt == "--use_https":
        config.enable_https()
    elif opt in ("-v", "--verbose"):
        config.set_verbose(True)
    elif opt == "--username":
        config.set_username(arg)
    elif opt == "--password":
        config.set_password(arg)
    elif opt == "--print-config":
        print_config = True

if print_config:
    config.print()
else:
    print(f'Running program with {config.threads} threads')

run_main()
