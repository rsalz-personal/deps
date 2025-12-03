#! /usr/bin/env python3

import csv, re, sys

name = "compdeps.csv"

pat = re.compile(".*\[(.*)\]")
fix = lambda s: s.replace(' ', '-').replace('-+-', '+')

# Header columns
sysdict = dict()
syslist = []

# I should really make a class that wraps the file, iterator, and
# this kind of thing.
def skip(line):
    return ' '.join(line).find("SKIP") > -1

# Parse open file `f` as a CSV file.
def open_csv(f):
    global sysdict, syslist
    reader = csv.reader(open(name))
    header = reader.__next__()[3:]
    if len(syslist) == 0:
        # Read and parse the header line.
        for sysname in header:
            m = pat.match(sysname)
            s = m[1] if m else sysname
            s = fix(s)
            sysdict[s] = 0
            syslist.append(s)
    return reader

# Find all self-reported circular dependencies
def self_reported():
    with open(name) as f:
        reader = open_csv(f)
        with open("self-reported.txt", "w") as out:
            for line in reader:
                if skip(line): continue
                me = fix(line[2])
                if me not in sysdict:
                    print(f"***{me} not found", file=sys.stderr)
                line = line[3:]
                for i in range(0, len(line)):
                    if line[i].find(',') != -1:
                        print(f"{me} : {syslist[i]}", file=out)

# Find duplicate entries
def find_duplicates():
    emails = dict()
    with open(name) as f:
        reader = open_csv(f)
        for k in sysdict.keys():
            sysdict[k] = []
        for line in reader:
            if skip(line): continue
            me = fix(line[2])
            sysdict[me].append(reader.line_num)
            emails[reader.line_num] = line[1]
    # Collect all items that appear more than once
    dups = [ k for k in sysdict.keys() if len(sysdict[k]) > 1 ]
    # Sort them by the number of items that mention them
    dups.sort(key=lambda d: len(sysdict[d]))
    with open("duplicate-reports.txt", "w") as out:
        for d in dups:
            l = sysdict[d]
            who = [ emails[n] for n in sysdict[d] ]
            print(f"{d} : {len(l)} : {l}\n\t{who}", file=out)

find_duplicates()
self_reported()
