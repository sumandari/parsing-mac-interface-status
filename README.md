## Generate Interface status report with MAC address vendor information on Cisco and Arista Switch
The aim of this script is to parse files (interface status and Mac address table) and generate an Excel report to show Interface status,description, Vlan, speed, and also Mac address of connected host/devices along with the Vendor name of each Mac addresses. 

## How to Generate the source files from Cisco/ Arista Switches


per session, the script will parse two below files, and the result will be Xlsx report generated afterward:
- File_a  : **iface-fact-hostnamex.json**
- File_b : **iface-MAC-hostnamex.txt**

### File_a : iface-fact-hostnamex.json
This file is generated using cisco and Arista ansible module repectively for each type of devices **arista.eos.eos_facts** and **cisco.ios.ios_facts**.\
It's where the script get **Hostname , Port number , Port Description , Interface status , and port speed** information.

Below is the snippet of the task on the ansible playbook : 

```YAML
###### Arista switch ####
  tasks:
    - name: get fact eos
      arista.eos.eos_facts:
        gather_subset:
        - all
        gather_network_resources:
        - interfaces
      become: yes
      when: ansible_network_os== "arista.eos.eos"
      register: iface_fact_eos

    - name: Generate temp file eos
      local_action:
        module: copy 
        content: |
          "{{iface_fact_eos}}"
        dest: ./tmp/iface-fact-{{ansible_net_hostname}}.json
      when: ansible_network_os== "arista.eos.eos"

#### Cisco Switch ###
    - name: get fact ios
      cisco.ios.ios_facts:
        gather_subset:
        - all
        gather_network_resources:
        - interfaces
      become: yes
      when: ansible_network_os== "cisco.ios.ios"
      register: iface_fact_ios
    - name: Generate temp file ios
      local_action:
        module: copy 
        content: |
          "{{iface_fact_ios}}"
        dest: ./tmp/iface_fact_{{ansible_net_hostname}}.json
      when: ansible_network_os== "cisco.ios.ios"
```


### File_b : iface_MAC_hostnamex.txt
This file is generated using cisco and Arista ansible module repectively for each type of devices **arista.eos.eos_facts** and **cisco.ios.ios_facts**\

This is where the script get **VLAN , Port number and connected MAC address** information.

Below is the snippet of the task on the ansible playbook : 

```YAML
    - name: run show mac table
      ios_command:
        commands: show mac address-table
      register: mactable

    - local_action: 
        module: copy
        content: "{{ mactable.stdout | replace('\\n', '\n') }}"
        dest: ./tmp/iface_MAC_{{ansible_net_hostname}}.txt
```

This script is also utilizing [mac-vendor-lookup](https://pypi.org/project/mac-vendor-lookup/) python library which will give Vendor information out of generated Mac Address.

## How to Run the script
### Run it directly from Python console

```
python3 parsing.py Filea[1],file_b[1] Filea[2],file_b[2] ...
```

### Run it via ansible task

this will parse the files generated on previous task if placed in the same playbook.

```
    - name: run the parsing and generate excel report
      ansible.builtin.script: parsing.py ./tmp/iface_fact_{{ansible_net_hostname}}.json,./iface_MAC_{{ansible_net_hostname}}.txt
      args:
        executable: python3
```


## Result

Microsoft Excel file report with list of Interface with port status , Mac vendor/address ,Vlan etc. Sheet are generated with its host name.



## Contributors:
- Me myself :P
- Ahmad Rifai (ripai.ahmad@gmail.com)
