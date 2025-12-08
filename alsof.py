#! /usr/bin/env python3

import argparse, csv, re, sys

name = "compdeps.csv"
what = []

pat = re.compile(".*\[(.*)\]")
fix = lambda s: s.replace(' ', '-').replace('-+-', '+')
skip = lambda line: ' '.join(line).find("SKIP") > -1

# A class that wraps the CSV reader class and includes file-opening
# with (context) and iterator support
class mycsv:
    COUNTS = 0
    ARRAY = 1
    def __init__(self, fname, what = COUNTS):
        try:
            self.src = open(fname)
        except OSError as e:
            print(f"Can't open {fname}: {e.strerror} (errno={e.errno})")
            raise SystemExit(1)
        self.reader = csv.reader(self.src)
        self.header = self.reader.__next__()[3:]
        self.syslist = []
        self.sysdict = dict()
        for sysname in self.header:
            m = pat.match(sysname)
            s = fix(m[1] if m else sysname)
            self.syslist.append(s)
            self.sysdict[s] = 0 if what == mycsv.COUNTS else []
    def __del__(self):
        if hasattr(self, 'src'):
            self.src.close()
    # with statement methods
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        pass
    # Iterator methods - pass it to the embedded CSV reader object.
    def __iter__(self):
        return self
    def __next__(self):
        while True:
            line = self.reader.__next__()
            if ' '.join(line).find("SKIP") == -1:
                self.sys = fix(line[2])
                return line
    # Methods
    def line_num(self):
        return self.reader.line_num

# Find all self-reported circular dependencies
def self_reported():
    with (mycsv(name) as f,
    open("self-reported.txt", "w") as out):
        for line in f:
            if self.sys not in f.sysdict:
                print(f"***{self.sys} not found", file=sys.stderr)
            line = line[3:]
            for i in range(0, len(line)):
                if line[i].find(',') != -1:
                    print(f"{self.sys} : {f.syslist[i]}", file=out)

# Find duplicate entries
def find_duplicates():
    emails = dict()
    with (mycsv(name, mycsv.ARRAY) as f,
    open("duplicate-reports.txt", "w") as out):
        for line in f:
            f.sysdict[f.sys].append(f.line_num())
            emails[f.line_num()] = line[1]
        # Collect all items that appear more than once
        dups = [ k for k in f.sysdict.keys() if len(f.sysdict[k]) > 1 ]
        # Sort them by the number of items that mention them
        dups.sort(key=lambda d: len(f.sysdict[d]))
        for d in dups:
            l = f.sysdict[d]
            who = [ emails[n] for n in f.sysdict[d] ]
            print(f"{d} : {len(l)} : {l}\n\t{who}", file=out)

def merge():
    with open(name) as f:
        lines = f.readlines()
    print(len(lines))

# Parse JCL.
parser = argparse.ArgumentParser(
                prog='alsof',
                description='ALSOF CIRCDEP survey results parser')
parser.add_argument('-f', '-in', dest='name', default=name,
                    help='Input file')
parser.add_argument('-d', '-dups', action='store_true',
                    help='Report duplicate entries')
parser.add_argument('-m', '-merge', action='store_true',
                    help='Merge dupicates to <infile>.new')
parser.add_argument('-s', '-self', action='store_true',
                    help='List self-reported circular dependencies')
d = vars(parser.parse_args())

# Import settings, act on them.
name = d['name']
if d['d']:
    find_duplicates()
if d['m']:
    merge()
if d['s']:
    self_reported()
