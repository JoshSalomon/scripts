Copyright 2019, Josh Salomon, Redhat

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

==========================================================================================================

This tool is load tester on Quay servers/clusters
It generates load of pull and push requests in order to measure the performance that Quay cluster provides to the client.

Usage: quay_load.py command OPTIONS
    Commands:
      pull       Perform load stress on the quay cluster (mostly pull requests and some pushes'
      push       Upload random images into quay registry (fill up the registry with data)'

For more information run 
quay_load.py command -h | --help

User and password: defaults are currently stores in file quay_constants.py (TEST_USERNAME and TEST_PWD) - but they can be changed from the command line.

Quay cluster ip address(es) -

TBD

DISCLAIMER:
This script was developed as a convenience tool for me, and I happily share it according to the MIT license. It is not meant to be productized by any means. If you feel you can use it for your purpose, feel free to do it and change it, If you have questions drop me an email, but for the time being I do not plan to maintain it as a robust tool for the public.
