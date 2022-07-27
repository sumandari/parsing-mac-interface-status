import ast
import errno
import os
import re
import sys
from pathlib import Path

from openpyxl import load_workbook, Workbook
from mac_vendor_lookup import AsyncMacLookup, MacLookup


FIELDNAMES = [
    'hostname',
    'port',
    'name',
    'status',
    'vlan',
    'duplex',
    'speed',
    'macAddress',
    'macVendor'
]
STATUS = 'connected'


def check_if_exist(filename):
    """The name already describes the function."""

    file = Path(filename)
    if not file.is_file():
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            filename
        )
    return file


def get_port_alias(port):
    """Get the alias name for a port.

    e.g port: Ethernet123, mac_alias: Et123
    """

    port_name_pattern = re.findall(
        r'([a-zA-Z]+)([0-9]+)',
        port
    )
    return port_name_pattern[0][0][0:2] + port_name_pattern[0][1]


def lookup_mac_vendor(macaddress):
    """Get the vendor name."""

    mac = MacLookup()
    return mac.lookup(macaddress)


def parsing_mac_address(file):

    print("Start parsing mac address...")

    macs = {}
    with open(file) as f:
        lines = f.readlines()
        for _ in lines[5:-1]:
            if _.startswith("Total Mac Addresses for this criterion:"):
                break
            line = _.split()
            vlan = line[0]
            mac = line[1]
            mac_type = line[2]
            port = line[3]
            # only get the "STATIC" mac address.
            if vlan and mac and port and mac_type == 'STATIC':
                try:
                    mac_vendor = lookup_mac_vendor(mac)
                except Exception as e:
                    print('exception', e)
                    mac_vendor = ''

                macs[port] = {
                    'vlan': vlan,
                    'mac': mac,
                    'macVendor': mac_vendor
                }
    return macs


def parsing_interface(iface, mac_address):
    """Parsing files"""

    print("Start parsing interface...")

    result = []
    with open(iface) as f:
        line = f.readline()
        data = ast.literal_eval(line.strip()[1:-1])
        if not isinstance(data, dict):
            print(f"Invalid file format: {iface}.")
            exit(1)

        ifaces = data.get('ansible_facts', None)
        hostname = ifaces.get('ansible_net_hostname', None)

        try:
            interfaces = ifaces['ansible_network_resources']['interfaces']
            iface_data = ifaces['ansible_net_interfaces']
        except KeyError as e:
            print("Invalid interfaces data.", e)
            exit(1)

        parsed_macs = parsing_mac_address(mac_address)
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

                port_alias = get_port_alias(port)
                if port_alias in parsed_macs:
                    vlan = parsed_macs[port_alias]['vlan']
                    mac = parsed_macs[port_alias]['mac']
                    mac_vendor = parsed_macs[port_alias]['macVendor']

                result.append((
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
    return result


def save_to_xlsx(iface, mac_addres, output):
    """Save the parsed interfaces and mac addresses data in xlsx file."""

    data = parsing_interface(iface, mac_addres)
    hostname = f"{data[0][0]}"
    wb = load_workbook(output)
    wb.create_sheet(title=hostname)
    sheet = wb[hostname]
    sheet.append(FIELDNAMES)
    for row in data:
        sheet.append(row)
    wb.save(output)


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3:
        raise TypeError(
            "Command must be: parsing.py <iface1.txt,macs1.txt> "
            "[<iface2.txt,macs2.txt>...] <output.xlsx>"
        )

    output = args[-1]
    if not Path(output).suffix == ".xlsx":
        raise TypeError("Output file must be .xlsx!")
    wb = Workbook()
    wb.save(f'{output}')

    for arg in args[1:-1]:
        files = arg.split(',')
        iface = check_if_exist(files[0])
        mac_address = check_if_exist(files[1])

        if iface and mac_address:
            save_to_xlsx(iface, mac_address, output)
