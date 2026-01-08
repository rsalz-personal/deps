#! /usr/bin/env python3

import argparse, csv, re, sys
from contextlib import redirect_stdout

name = "compdeps.csv"
what = []

pat = re.compile(".*\[(.*)\]")
skip = lambda line: ' '.join(line).find("SKIP") > -1

# A dictionary mapping names from the CSV file to names that are
# useable in MemGraph.
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
    "Prometheus + Alert Manager" : "Prometheus_AlertManager",
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
    # List of (me, i-depend-on) tuples.
    pairs = []
    who = dict()
    when = dict()
    with (CSVReader(name) as f,
    open("self-reported.txt", "w") as out):
        for line in f:
            if f.sys not in f.systems:
                print(f"***{f.sys} not found", file=sys.stderr)
            when[f.sys] = line[0][0:9].replace('/', '-')
            who[f.sys] = line[1]
            line = line[3:]
            for i in range(0, len(line)):
                # Find all "depends,me-depend" entries and record them
                if line[i].find(',') != -1:
                    pairs.append((f.sys,f.syslist[i]))
                    print(f"{f.sys} : {f.syslist[i]}", file=out)

    # Get a unique list of everyone we recorded
    names = [ k for (k,v) in pairs ]
    names.extend([ v for (k,v) in pairs ])
    names = set(names)

    # Create the database.
    with open("self-reported.cypherl", "w") as mg:
        with redirect_stdout(mg):
            ids = dict()
            for (i,n) in enumerate(names):
                ids[n] = i + 1
                wn = when.get(n, 'XXX')
                wo = who.get(n, 'XXX')
                print(f'CREATE ({n}:Sys {{id:{i+1}, name:"{n}"'
                      f', when:"{wn}", who:"{wo}"'
                      f'}} );')
            #print('LOAD CSV from "file:///Users/rsalz/git/alsof-circdep/self-reported.csv" WITH HEADER as dep')
            print('UNWIND [')
            for sys,dep in pairs[:-2]:
                print(f'  {{from:{ids[sys]}, to:{ids[dep]}}},')
            (sys,dep) = pairs[-1]
            print(f'  {{from:{ids[sys]}, to:{ids[dep]}}}')
            print('] AS dep');
            print('     MATCH (a {id: dep.from}), (b {id: dep.to})')
            print('     MERGE (a)-[:DEPENDS_ON]->(b), (b)-[:DEPENDS_ON]->(a);')
            print('     RETURN count(a);')
            print('MATCH p = (n)-[:DEPENDS_ON*2..10]->(n)')
            print('RETURN p;')

    # Create the CSV file of dependencies
    with open("self-reported.csv", "w") as csv:
        with redirect_stdout(csv):
            print('from,to')
            for sys,dep in pairs[:-2]:
                print(f'{ids[sys]}, {ids[dep]}')
            (sys,dep) = pairs[-1]
            print(f'{ids[sys]}, {ids[dep]}')

# Find duplicate entries
def find_duplicates():
    emails = dict()
    with (CSVReader(name, CSVReader.ARRAY) as f,
    open("duplicate-reports.txt", "w") as out):
        for line in f:
            f.systems[f.sys].append(f.line_num())
            emails[f.line_num()] = line[1]
        # Collect all items that appear more than once
        dups = [ k for k in f.systems.keys() if len(f.systems[k]) > 1 ]
        # Sort them by the number of items that mention them
        dups.sort(key=lambda d: len(f.systems[d]))
        for d in dups:
            l = f.systems[d]
            who = [ emails[n] for n in f.systems[d] ]
            print(f"{d} : {len(l)} : {l}\n\t{who}", file=out)

def merge_lines(merged, addl):
    pass

# Merge duplicate entries
def merge():
    newname = 'new-' + name
    merged = dict()
    with CSVReader(name) as f:
        lines = [ f.header ]
        for line in f:
            first = f.systems.get(f.sys, None)
            if first is None:
                merged[f.sys] = line
                lines.append(line)
            else:
                ### MERGE FIELDS
                merge_lines(first, line)
                line[0] = 'SKIP MERGED ' + line[0]
                lines.append(line)
    with open(newname, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(lines)
        for k,v in merged:
            write.writerow(v)


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
