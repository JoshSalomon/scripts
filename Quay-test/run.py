#!/usr/bin/python3

from main import run_main
import sys, getopt

# todo - add command line for number of iterations over the inventory
def usage():
    print(f'Usage: {sys.argv[0]} [ <-t | --threads> num_threads] [-h | --help]')


n_threads = 0
try:
    opts, args = getopt.getopt(sys.argv[1:], "t:h", ["threads=", "help"])
except getopt.GetoptError:
    usage()
    sys.exit(2)

for opt, arg in opts:
    if opt in ('-h', '--help'):
        usage()
        sys.exit()
    elif opt in ("-t", "--threads"):
        n_threads = int(arg)
    print(f'Running program with {n_threads} threads')
if n_threads == 0:
    run_main()
else:
    run_main(n_threads)
