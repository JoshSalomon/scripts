#!/home/jsalomon/.virtualenvs/venv/bin/python3.7
# ### !/usr/bin/python3
from config import Command
import sys
import getopt
import config
import logging
import ipaddress
from main import run_pull_load, run_push_load

# todo - add chunk size fof push
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
    print('-s, --seconds <num>    Time to run the test in seconds. The test completes when the time is reached')
    print('--quay-ips <ip list>   List of IP addresses of the Quay server (comma separated)')
    print('                       Default is <%s>' % config.quay_ips_as_str())
    print('--quay-port <num>      The port on which Quay server listens')
    print('                       Default is none')
    print('--use_https            Use HTTPS protocol to connect to quay instead of http')
    print('                       Default %s' % config.verbose)
    print('--max-tags <num>       Limit the number of tags retrieved before the pull test (to  save time in debug)')
    print('                       Default is %d (<=0 - read all the tags in the repository)' % config.max_tags)
    print('-v, --verbose          Print more info to the console')
    print('                       Default is %s' % config.verbose)
    print('--verbose-on-error     Start printing more info after encountering errors')
    print('                       Default is %s' % config.verbose_on_error)
    print('--username <string>    The username for logging into Quay')
    print('                       Default is %s' % config.username)
    print('--password <string>    Password for the login')
    print('--print-config         Print configuration before starting')
    print('-h, --help             Print this message, and exit')
    return


def usage_push():
    print(f'Usage: {sys.argv[0]} push [OPTIONS]')
    print('   Fill up the Quay registry by uploading random images to the registry ')
    print('   This operation is limited by either number of images or the total size of images ')
    print('   uploaded to the registry')
    print('Options:')
    print('-t, --threads          Number of concurrent threads in this test')
    print('                       Default %d' % config.threads)
    print('--push-size-gb <num>   The total size of images to upload')
    print('                       Default is %.01f GB' % config.push_size_gb)
    print('--images <num>         Number of images to upload (used only if no size-gb is given)')
    print('                       Default is %d' % config.num_upload_images)
    print('--wait <num>           Time to wait between pull ops in seconds')
    print('                       Default is 0 (no wait)')
    print('--quay-ips <ip list>   List of IP addresses of the Quay server (comma separated)')
    print('                       Default is <%s>' % config.quay_ips_as_str())
    print('--quay-port <num>      The port on which Quay server listens')
    print('                       Default is none')
    print('--use_https            Use HTTPS protocol to connect to quay instead of http')
    print('                       Default %s' % config.verbose)
    print('-v, --verbose          Print more info to the console')
    print('                       Default is %s' % config.verbose)
    print('--verbose-on-error     Start printing more info after encountering errors')
    print('                       Default is %s' % config.verbose_on_error)
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
             "quay-ips=",
             "quay-port=",
             "use_https",
             "verbose",
             "username=",
             "password=",
             "print-config",
             "verbose-on-error",
             "dont-run",
             "help"]


print_config = False


def parse_opts(cmd):
    global short_opts
    global long_opts
    if cmd == Command.PULL:
        short_opts = short_opts + "c:s:"
        long_opts.append("cycles=")
        long_opts.append("seconds=")
        long_opts.append("max-tags=")
    elif cmd == Command.PUSH:
        long_opts.append("push-size-gb=")
        long_opts.append("images=")
        long_opts.append("wait=")
    try:
        opts, args = getopt.getopt(sys.argv[2:], short_opts, long_opts)
        for opt, arg in opts:
            if opt in ("-t", "--threads"):
                config.threads = int(arg)
            elif opt in ("-c", "--cycles"):
                config.cycles = int(arg)
            elif opt == "--quay-ips":
                ips = arg.split(",")
                if len(ips) > 0:
                    for i in range(len(ips)):
                        ip_value_error = False
                        try:
                            ipaddress.ip_address(ips[i])
                        except ValueError as ve:
                            print(f'Error: {ve}')
                            ip_value_error = True
                    if ip_value_error:
                        sys.exit(1)
                    config.quay_ips = ips
                    # logging.debug(f' *** set quay ips to {config.quay_ips_as_str()}')
            elif opt == "--quay-port":
                config.quay_port = int(arg)
            elif opt == "--use-https":
                config.use_https()
            elif opt in ("-v", "--verbose"):
                config.verbose = True
            elif opt == "--verbose-on-error":
                config.verbose_on_error = True
            elif opt == "--username":
                config.username = arg
            elif opt == "--password":
                config.password = arg
            elif opt == "--print-config":
                global print_config
                print_config = True
            elif opt == "--dont-run":
                config.dont_run = True
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
                config.cycles = int(arg)
            elif opt in ("-s", "--seconds"):
                config.seconds_to_end = int(arg)
            elif opt == "--max-tags":
                config.max_tags = int(arg)
            #
            # PUSH only options
            #
            elif opt == "--push-size-gb":
                config.push_size_gb = int(arg)
            elif opt == "--images":
                config.num_upload_images = int(arg)
            elif opt == "--wait":
                config.wait_between_ops = int(arg)
            else:
                logging.error(f" Illegal option {opt} for command {sys.argv[1]}")
                assert False

    except getopt.GetoptError:
        logging.basicConfig(level=logging.INFO, format='[%(levelname)-8s] %(message)s', )
        logging.error("Error parsing command line arguments, exiting")
        if command == Command.PUSH:
            usage_push()
        elif command == Command.PULL:
            usage_pull()
        else:
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

if config.dont_run:
    sys.exit(0)

if command == Command.PULL:
    run_pull_load()
elif command == Command.PUSH:
    run_push_load()
else:
    assert False
