#! /usr/bin/env python3

import argparse, csv, re, sys
from contextlib import redirect_stdout

name = "compdeps.csv"

pat = re.compile(r".*\[(.*)\]")
skip = lambda line: ' '.join(line).find("SKIP") > -1
getwhen = lambda line: line[0][0:10].replace('/', '-')
getwho = lambda line: line[1].replace('@akamai.com', '')

##  A dictionary mapping names from the CSV file to names that are
##  useable in MemGraph.
renames = {
    "Admin/BP" : "AdminBP",
    "Akamai Cloud Pulse" : "AkamaiCloudPulse",
    "app-aclp (stats + log)" : "app_aclp",
    "app-blockstorage microservice" : "app_blockstorage",
    "app-cloud-net-api microservice" : "app_cloud_net_api",
    "app-dbaas (sg + aiven)" : "app_dbaas",
    "app-infra microservice" : "app_infra",
    "app-k8s microservice" : "app_k8s",
    "app-nlb microservice" : "app_nlb",
    "app-sre microservice" : "app_sre",
    "Apt Cachers" : "AptCachers",
    "Apt Repo" : "AptRepo",
    "Block Storage" : "BlockStorage",
    "bolt-monitor" : "BoltMonitor",
    "BP/External API" : "BPExternalAPI",
    "Build Box (Guest Kernels)" : "BuildBox",
    "CF-API (billing)" : "CF_API_billing",
    "Cloud Firewall" : "CloudFirewall",
    "CloudIAM " : "CloudIAM",
    "Cloud Manager" : "CloudManager",
    "Community Site" : "CommunitySite",
    "Compute Core (Vbin, host stack)" : "ComputeCore",
    "Consul/Service Mesh" : "Consul_ServiceMesh",
    "Customer Recursive Resolvers" : "CustomerRecursiveResolvers",
    "DBaaS Analytics (being replaced by Akamai Cloud Pulse)" : "DBaaSAnalytics",
    "Dc-turnup-testing" : "DCTurnupTesting",
    "DDoS Alerting and Mitigation" : "DDoSAlertingandMitigation",
    "DDoS-Routers" : "DDoSRouters",
    "Developer Experience" : "DeveloperExperience",
    "Dhcp-unnumbered" : "DhcpUnnumbered",
    "Dhcp6-unnumbered" : "Dhcp6Unnumbered",
    "Domain Manager" : "DomainManager",
    "ELF Services" : "ELFServices",
    "Fleet Manager" : "FleetManager",
    "FRR-Reloader" : "FRR_Reloader",
    "Github (inc bits)" : "Github_and_bits",
    "github actions" : "github_actions",
    "Hosting Database and ProxySQL" : "HostingDB_ProxySQL",
    "Image Service (incl MIPS/Midas/Imagenext)" : "ImageService",
    "Infra Boxes" : "InfraBoxes",
    "Ingress Hosts" : "IngressHosts",
    "Internal CA / SSL" : "InternalCA_SSL",
    "kvdata + iptables" : "kvdata_iptables",
    "Linode Jira" : "LinodeJira",
    "Linode Login" : "LinodeLogin",
    "Linode-Capirca" : "LinodeCapirca",
    "Linode/goblin" : "LinodeGoblin",
    "Lish/Glish/Weblish/etc" : "Lish_etc",
    "LKE-E" : "LKE_E",
    "LoadBalancers (api, cloud login, etc)" : "LoadBalancers",
    "Log Collect" : "LogCollect",
    "Longview (being replaced by Cloud Pulse)" : "Longview",
    "Machine-Tools" : "MachineTools",
    "Management Resolvers" : "ManagementResolvers",
    "Metadata (in Backups)" : "MetadataBackups",
    "Migration / Cloning" : "MigrationCloning",
    "Authorative Nameservers" : "AuthorativeNameservers",
    "Netbox-circuits" : "Netbox_Circuits",
    "Network Config Backups" : "NetworkConfigBackups",
    "o11y-firechief-updater" : "o11y_firechief_updater",
    "Object Storage Gen 1" : "ObjectStorageGen1",
    "Object Storage Gen 2" : "ObjectStorageGen2",
    "Open Telemetry" : "OpenTelemetry",
    "Ops Jenkins" : "OpsJenkins",
    "osa (Object Storage API) microservice" : "ObjectStorageAPI",
    "Outbound mail" : "OutboundMail",
    "Prometheus + Alert Manager" : "PrometheusAlertMgr",
    "Provisioning API" : "ProvisioningAPI",
    "Rad-Unumbered" : "RadUnumbered",
    "Reseller Support API" : "ResellerSupportAPI",
    "Route Servers (Golinject Routeservers)" : "RouteServers",
    "Smartwall TDD Systems" : "SmartwallTDDSystems",
    "Tagg Boxes" : "TaggBoxes",
    "VM Allocator" : "VMAllocator",
    "Web Boxes (www)" : "WebBoxes",
    "Net L4 LB" : "NetL4LB",
}

fix = lambda s: renames.get(s, s)


##  A class that wraps the CSV reader class and includes file-opening
##  with (context) and iterator support
class CSVReader:
    COUNTS = 0
    ARRAY = 1
    def __init__(self, fname, what = COUNTS):
        try:
            self.src = open(fname)
        except OSError as e:
            print(f"Can't open {fname}: {e.strerror} (errno={e.errno})")
            raise SystemExit(1)
        self.reader = csv.reader(self.src)
        self.header = self.reader.__next__()
        self.syslist = []
        self.systems = dict()
        for sysname in self.header[3:]:
            m = pat.match(sysname)
            s = fix(m[1] if m else sysname)
            self.syslist.append(s)
            self.systems[s] = 0 if what == CSVReader.COUNTS else []
    def __del__(self):
        if hasattr(self, 'src'):
            self.src.close()
    # "with" statement (context) methods
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

##
##
##

##  Find all self-reported circular dependencies
def self_reported():
    # List of (me, i-depend-on) tuples.
    pairs = []
    when = dict()
    who = dict()
    with (CSVReader(name) as f,
          open("self-reported.txt", "w") as out):
        for line in f:
            if f.sys not in f.systems:
                print(f"***{f.sys} not found", file=sys.stderr)
                continue
            when[f.sys] = getwhen(line)
            who[f.sys] = getwho(line)
            line = line[3:]
            for i in range(0, len(line)):
                # Find all "depend-on,me-depend-on" entries and record them
                if line[i].find(',') != -1:
                    print(f"{f.sys} : {f.syslist[i]}", file=out)
                    pairs.append((f.sys,f.syslist[i]))

    # Get a unique list of everyone we recorded
    names = [ k for (k,v) in pairs ]
    names.extend([ v for (k,v) in pairs ])
    names = set(names)

    # Create the nodes.
    with open("mg/self-nodes.csv", "w") as mg:
        with redirect_stdout(mg):
            print('id,name,when,who')
            ids = dict()
            for (i,n) in enumerate(names, 1):
                ids[n] = i
                wn = when.get(n, 'XXX')
                wo = who.get(n, 'XXX')
                print(f'{i},"{n}","{wn}","{wo}"')

    # Create the depends-on table
    with open("mg/self-edges.csv", "w") as mg:
        with redirect_stdout(mg):
            print('from,to')
            for fr,to in pairs:
                print(f'{ids[fr]},{ids[to]}')
                print(f'{ids[to]},{ids[fr]}')

##  Find duplicate entries
def find_duplicates():
    emails = dict()
    with (CSVReader(name, CSVReader.ARRAY) as f,
          open("duplicate-reports.txt", "w") as out):
        for line in f:
            f.systems[f.sys].append(f.line_num())
            emails[f.line_num()] = getwho(line)
        # Collect all items that appear more than once
        dups = [ k for k in f.systems.keys() if len(f.systems[k]) > 1 ]
        # Sort them by the number of items that mention them
        dups.sort(key=lambda d: len(f.systems[d]))
        for d in dups:
            l = f.systems[d]
            who = [ emails[n] for n in f.systems[d] ]
            print(f"{d} : {len(l)} : {l}\n\t{who}", file=out)

##  Merge two fields, return the new value
def merge_field(a, b):
    # If fields have the same value, return a
    if a == b:
        return a
    # If either is empty, return the other one
    if b == '':
        return a
    if a == '':
        return b;
    # If either field is multi-valued, return it
    if a.find(',') > -1:
        return a
    if b.find(',') > -1:
        return b
    return 'I depend on this,This depends on me'

##  Merge duplicate entries
def merge():
    merged = dict()
    with CSVReader(name) as f:
        header = f.header
        for line in f:
            first = merged.get(f.sys, None)
            if first is None:
                merged[f.sys] = line
                continue
            # Merge the fields
            first[1] += '+' + getwho(line)
            for i in range(2, len(first)):
                first[i] = merge_field(first[i], line[i])
    with open('merged-' + name, 'w') as f:
        wr = csv.writer(f)
        wr.writerow(header)
        for v in merged.values():
            wr.writerow(v)

##  Find circular dependencies.
def cycles():
    # Open the output files, generate the header line for each
    with (open("mg/nodes.csv", "w") as nodes,
          open("mg/edges.csv", "w") as edges):
        print("name,id,when,who", file=nodes)
        print("from,to", file=edges)
        with CSVReader(name) as f:
            for line in f:
                when = getwhen(line)
                who = getwho(line)
                me = f.line_num()
                print(f"{f.sys},{me},{when},{who}", file=nodes)
                line = line[2:]
                for i in range(0, len(line)):
                    if line[i].find("I depend on") > -1:
                        print(f"{me},{i}", file=edges)
                    if line[i].find("depends on me") > -1:
                        print(f"{i},{me}", file=edges)

##  Parse JCL.
parser = argparse.ArgumentParser(
                prog='alsof',
                description='ALSOF CIRCDEP survey results parser')
parser.add_argument('-f', '-in', dest='name', default=name,
                    help='Input file')
parser.add_argument('-c', '-cycles', action='store_true',
                    help='Generate data for full circular dependencies')
parser.add_argument('-d', '-dups', action='store_true',
                    help='Report duplicate entries')
parser.add_argument('-m', '-merge', action='store_true',
                    help='Merge dupicates to merged-<infile>')
parser.add_argument('-s', '-self', action='store_true',
                    help='List self-reported circular dependencies')
d = vars(parser.parse_args())

##  Import settings, act on them.
name = d['name']
if d['d']:
    find_duplicates()
if d['m']:
    merge()
if d['s']:
    self_reported()
if d['c']:
    cycles()
