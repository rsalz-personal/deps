#! /usr/bin/env python3

import csv, re, sys

name = "compdeps.csv"

pat = re.compile(".*\[(.*)\]")
fix = lambda s: s.replace(' ', '-').replace('-+-', '+')
skip = lambda line: ' '.join(line).find("SKIP") > -1

class mycsv:
    COUNTS = 0
    ARRAY = 1
    def __init__(self, fname, what = COUNTS):
        self.src = open(fname)
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
        self.src.close()
    # Iterator methods
    def __iter__(self):
        return self
    def __next__(self):
        while True:
            line = self.reader.__next__()
            if ' '.join(line).find("SKIP") == -1:
                line[2] = fix(line[2])
                return line
    # with statement methods
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        pass
    # Methods
    def line_num(self):
        return self.reader.line_num

# Find all self-reported circular dependencies
def self_reported():
    with (mycsv(name) as f,
    open("self-reported.txt", "w") as out):
        for line in f:
            me = line[2]
            if me not in f.sysdict:
                print(f"***{me} not found", file=sys.stderr)
            line = line[3:]
            for i in range(0, len(line)):
                if line[i].find(',') != -1:
                    print(f"{me} : {f.syslist[i]}", file=out)

# Find duplicate entries
def find_duplicates():
    emails = dict()
    with (mycsv(name, mycsv.ARRAY) as f,
    open("duplicate-reports.txt", "w") as out):
        for line in f:
            f.sysdict[line[2]].append(f.line_num())
            emails[f.line_num()] = line[1]
        # Collect all items that appear more than once
        dups = [ k for k in f.sysdict.keys() if len(f.sysdict[k]) > 1 ]
        # Sort them by the number of items that mention them
        dups.sort(key=lambda d: len(f.sysdict[d]))
        for d in dups:
            l = f.sysdict[d]
            who = [ emails[n] for n in f.sysdict[d] ]
            print(f"{d} : {len(l)} : {l}\n\t{who}", file=out)

find_duplicates()
self_reported()
