import errno
import os
import sys
from pathlib import Path


def parsing(hostname, iface, mac_address, output):
    """Parsing files"""

    print("Start parsing...")

    # Eventhough the files extension is tsv, it turns out that
    # they have space as separator instead of tab.
    # If you can provide files in "real" tsv format,
    # we can parse it in a better way
    with open(hostname, 'r') as f:
        hostname_value = f.readline().split()[-1]
        print(f"Hostname: '{hostname_value}'")
    with open(mac_address) as f:
        lines = f.readlines()
    for _ in lines[5:-1]:
        if _.startswith("Total Mac Addresses for this criterion:"):
            break
        line = _.split()
        vlan = line[0]
        port = line[3]
        print(f"Vlan: '{vlan}', Port: '{port}")


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
    if len(args) < 5:
        raise TypeError(
            f"Command must be: parsing.py <file1> <file2> <file3> "
            "<output_filename_dot_tsv>"
        )
    hostname = check_if_exist(args[1])
    iface = check_if_exist(args[2])
    mac_address = check_if_exist(args[3])
    output = args[4]

    if hostname and iface and mac_address:
        parsing(hostname, iface, mac_address, output)
