#!/home/jsalomon/.virtualenvs/venv/bin/python3.7
# ### !/usr/bin/python3
from config import Command
import sys
import getopt
import config
import logging
from main import run_pull_load, run_push_load

config = config.Config()


def usage_pull():
    print(f'Usage: {sys.argv[0]} pull [OPTIONS]')
    print('   Load the Quay registry by constantly pulling images from the registry, each thread pulls ')
    print('   all the images it can read from the repository n time according to the --cycles parameter.')
    print('   In parallel other threads are pulling images to the registry at a rate smaller than 5% of the')
    print('   total load.')
    print('Options:')
    print('-t, --threads          Number of concurrent threads in this test')
    print('                       Default %d' % config.threads)
    print('-c, --cycles           Number of cycles over the entire registry each thread performs')
    print('                       Default %d' % config.cycles)
    print('--quay-ip <ipaddress>  IP address of the Quay server')
    print('                       Default %s' % config.quay_ip)
    print('--quay-port <num>      The port on which Quay server listens')
    print('                       Default is none')
    print('--use_https            Use HTTPS protocol to connect to quay instead of http')
    print('                       Default %s' % config.verbose)
    print('-v, --verbose          Print more info to the console')
    print('                       Default is %s' % config.verbose)
    print('--username <string>    The username for logging into Quay')
    print('                       Default is %s' % config.username)
    print('--password <string>    Password for the login')
    print('--print-config         Print configuration before starting')
    print('-h, --help             Print this message, and exit')
    return


def usage_push():
    print(f'Usage: {sys.argv[0]} pull [OPTIONS]')
    print('   Fill up the Quay registry by uploading random images to the registry ')
    print('   This operation is limited by either number of images or the total size of images ')
    print('   uploaded to the registry')
    print('Options:')
    print('-t, --threads          Number of concurrent threads in this test')
    print('                       Default %d' % config.threads)
    print('--push-size-gb <num>   the total size of images to upload')
    print('                       Default is %.01f GB' % config.push_size_gb)
    print('--images <num>         number of images to upload (used only if no size-gb is given)')
    print('                       Default is %d' % config.num_upload_images)
    print('--quay-ip <ipaddress>  IP address of the Quay server')
    print('                       Default %s' % config.quay_ip)
    print('--quay-port <num>      The port on which Quay server listens')
    print('                       Default is none')
    print('--use_https            Use HTTPS protocol to connect to quay instead of http')
    print('                       Default %s' % config.verbose)
    print('-v, --verbose          Print more info to the console')
    print('                       Default is %s' % config.verbose)
    print('--username <string>    The username for logging into Quay')
    print('                       Default is %s' % config.username)
    print('--password <string>    Password for the login')
    print('--print-config         Print configuration before starting')
    print('-h, --help             Print this message, and exit')
    return


def usage():
    print(f'Usage: {sys.argv[0]} command [OPTIONS]')
    print('Commands:')
    print('  pull       Perform load stress on the quay cluster (mostly pull requests and some pushes')
    print('  push       Upload random images into quay registry (fill up the registry with data)')
    return


short_opts = "t:vh"

long_opts = ["threads=",
             "quay-ip=",
             "quay-port=",
             "use_https",
             "verbose",
             "username=",
             "password=",
             "print-config",
             "help"]


print_config = False


def parse_opts(cmd):
    global short_opts
    global long_opts
    if cmd == Command.PULL:
        short_opts = short_opts + "c:"
        long_opts.append("cycles=")
    elif cmd == Command.PUSH:
        long_opts.append("push-size-gb=")
        long_opts.append("images=")
    try:
        opts, args = getopt.getopt(sys.argv[2:], short_opts, long_opts)
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
                global print_config
                print_config = True
            elif opt in ("-h", "--help"):
                if cmd == Command.PULL:
                    usage_pull()
                elif cmd == Command.PUSH:
                    usage_push()
                else:
                    assert False
                exit(0)
            #
            # PULL only options
            #
            elif opt in ("-c", "--cycles"):
                config.set_cycles(int(arg))
            #
            # PUSH only options
            #
            elif opt == "--push-size-gb":
                config.set_push_size_gb(arg)
            elif opt == "--images":
                config.set_num_upload_images(arg)
            else:
                assert False

    except getopt.GetoptError:
        logging.basicConfig(level=logging.INFO, format='[%(levelname)-8s] %(message)s', )
        logging.error("Error parsing command line arguments, exiting")
        usage()
        sys.exit(2)


command = None
try:
    if len(sys.argv) > 1:
        if sys.argv[1] == "pull":
            command = Command.PULL
        elif sys.argv[1] == "push":
            command = Command.PUSH
        else:
            usage()
            sys.exit()
        parse_opts(command)
    else:
        usage()
        sys.exit()

except getopt.GetoptError:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)-8s] %(message)s', )
    logging.error("Error parsing command line arguments, exiting")
    usage()
    sys.exit(2)

#
# First thing find -h and print usage with the default values
#


if print_config:
    config.print(command)
else:
    print(f'Running program with {config.threads} threads')

if command == Command.PULL:
    run_pull_load()
elif command == Command.PUSH:
    run_push_load()
else:
    assert False
