## Parse Mac address interfaces

## How to retrieve the files from Cisco's/ Arista's API
.........

Mac address file generate : 
    - local_action: 
        module: copy
        content: "{{ outputmac.stdout | replace('\\n', '\n') }}"
        dest: ./tmp/mac_{{ansible_net_hostname}}.txt

## Contributors:
- Me myself :P
- Ahmad Rifai (ripai.ahmad@gmail.com)
