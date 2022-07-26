import ast
import csv
import errno
import os
import re
import sys
from pathlib import Path
from telnetlib import STATUS

from openpyxl import Workbook

from mac_vendor_lookup import AsyncMacLookup, MacLookup



SHEETNAME = 'output'
STATUS = 'connected'


def lookup_mac_vendor(macaddress):
    # The mac_vendor_lookup library provides async class version,
    # but somehow it always throws an exception:
    # RuntimeWarning: coroutine 'lookup_mac_vendor' was never awaited.
    # probably we can address it sometime... someday...
    mac = MacLookup()
    return mac.lookup(macaddress)


def parsing(iface, mac_address, output):
    """Parsing files"""

    print("Start parsing...")

    wb = Workbook()
    wb.create_sheet(index=0, title=SHEETNAME)
    sheet = wb[SHEETNAME]

    macs = []
    with open(mac_address) as f:
        lines = f.readlines()
        for _ in lines[5:-1]:
            if _.startswith("Total Mac Addresses for this criterion:"):
                break
            line = _.split()
            vlan = line[0]
            mac = line[1]
            mac_type = line[2]
            port = line[3]
            if vlan and mac and port and mac_type == 'STATIC':
                macs.append((port, mac, vlan))
            print(macs)

    ifaces = {}
    with open(iface) as f:
        line = f.readline()
        ifaces = ast.literal_eval(line.strip()[1:-1])
        if not isinstance(ifaces, dict):
            print(f"Invalid file format: {iface}.")
            exit(1)
        ifaces = ifaces.get('ansible_facts', None)

    with open(output, mode='w') as f:
        fieldnames = ['hostname', 'port', 'name', 'status',
                      'vlan', 'duplex', 'speed', 'macAddress', 'macVendor']
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        sheet.append(fieldnames)

        hostname = ifaces.get('ansible_net_hostname', None)

        try:
            interfaces = ifaces['ansible_network_resources']['interfaces']
            iface_data = ifaces['ansible_net_interfaces']
        except KeyError:
            print("Invalid interfaces data.")
            exit(1)

        for interface in interfaces:
            try:
                port = interface['name']
                status = iface_data[port].get('operstatus', None)
                if not status or status != STATUS:
                    continue
                name = iface_data[port].get('description', None)
                
                duplex = iface_data[port].get('duplex', None)
                speed = iface_data[port].get('bandwidth', None)
                vlan = None
                mac = None
                mac_vendor = None
                if ifaces['ansible_net_neighbors'].get(port, None):
                    mac_array = ifaces['ansible_net_neighbors'][port]
                    mac = ",".join([_['host'] for _ in mac_array])

                    mac_vendor = lookup_mac_vendor(mac_array[0]['host'])

                    # e.g port = Ethernet123, mac_alias = Et123
                    port_name_pattern = re.findall(
                        r'([a-zA-Z]+)([0-9]+)',
                        port
                    )
                    port_alias = (port_name_pattern[0][0][0:2] +
                                  port_name_pattern[0][1])

                    # We'll need to refactor this into separated function!
                    # But later :P
                    for m in macs:
                        if port_alias in m and mac_array[0]['port'] in m:
                            vlan = m[2]

                writer.writerow({
                    'hostname': hostname,
                    'port': port,
                    'name': name,
                    'status': status,
                    'duplex': duplex,
                    'speed': speed,
                    'macAddress': mac,
                    'macVendor': mac_vendor,
                    'vlan': vlan,
                })

                sheet.append((
                    hostname,
                    port,
                    name,
                    status,
                    vlan,
                    duplex,
                    speed,
                    mac,
                    mac_vendor
                ))

            except KeyError as e:
                print(f"Invalid interfaces data in port {port}.", e.__str__())
            wb.save('output.xlsx')


def check_if_exist(filename):
    file = Path(filename)
    if not file.is_file():
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            filename
        )
    return file


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 4:
        raise TypeError(
            f"Command must be: parsing.py <file1> <file2> <output>"
        )
    iface = check_if_exist(args[1])
    mac_address = check_if_exist(args[2])
    output = args[3]

    if iface and mac_address:
        parsing(iface, mac_address, output)
