import nmap
import ipaddress
import os

def get_network_ranges():
    """Gets network interfaces and their associated IP ranges."""
    if os.name == 'nt':  # Windows
        import subprocess
        output = subprocess.check_output(['ipconfig', '/all']).decode()
        interfaces = {}
        current_interface = None
        for line in output.splitlines():
            line = line.strip()
            if line.endswith(':'):  # Interface name
                current_interface = line[:-1]
                interfaces[current_interface] = []
            elif 'IPv4 Address' in line and '(Preferred)' in line:
                ip_address = line.split(':')[1].strip().split('(')[0].strip()
                for line2 in output.splitlines():
                    line2 = line2.strip()
                    if 'Subnet Mask' in line2 and current_interface in output.splitlines()[output.splitlines().index(line)+1]:
                        subnet_mask = line2.split(':')[1].strip()
                        try:
                            network = ipaddress.ip_interface(f"{ip_address}/{subnet_mask}").network
                            interfaces[current_interface].append(str(network))
                        except ValueError:
                            pass
                
    elif os.name == 'posix': # Linux/macOS
        import netifaces
        interfaces = {}
        for interface in netifaces.interfaces():
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                for addr in addresses[netifaces.AF_INET]:
                    ip_address = addr['addr']
                    netmask = addr['netmask']
                    try:
                        network = ipaddress.ip_interface(f"{ip_address}/{netmask}").network
                        interfaces[interface] = [str(network)]
                    except ValueError:
                        pass
    else:
        print("Unsupported operating system.")
        return None
    return interfaces


def scan_network(network_range):
    """Scans the specified network range for live hosts and performs basic port/service detection."""
    nm = nmap.PortScanner()
    try:
        nm.scan(hosts=network_range, arguments='-sn -O -sV --script vuln')  # Add -O and -sV for OS and version detection
    except nmap.PortScannerError as e:
        print(f"Nmap scan error: {e}")
        return None

    online_hosts = []
    for host in nm.all_hosts():
        host_info = {'ip': host, 'hostname': nm[host].hostname(), 'ports': [],'os': None, 'services': []}

        if 'osmatch' in nm[host]:
            for osmatch in nm[host]['osmatch']:
                host_info['os'] = osmatch['name']

        for proto in nm[host].all_protocols():
            lport = nm[host][proto].keys()
            for port in lport:
                if nm[host][proto][port]['state'] == 'open':
                    service_info = {'port': port, 'protocol': proto, 'name': nm[host][proto][port]['name'], 'version': nm[host][proto][port].get('version', 'Unknown')}
                    host_info['services'].append(service_info)
                    host_info['ports'].append(port)

        online_hosts.append(host_info)
    return online_hosts

def display_scan_results(hosts):
    if not hosts:
        print("No online hosts found or scan failed.")
        return

    for host in hosts:
        print("-" * 30)
        print(f"IP: {host['ip']}")
        if host['hostname']:
            print(f"Hostname: {host['hostname']}")
        if host.get('os'):
            print(f"OS: {host['os']}")
        if host['ports']:
            print("Open Ports:")
            for service in host['services']:
                print(f"  {service['port']}/{service['protocol']}: {service['name']} (Version: {service['version']})")
        else:
            print("No open ports found.")
        print("-" * 30)

if __name__ == "__main__":
    network_ranges = get_network_ranges()
    if network_ranges:
        print("Available Network Ranges:")
        for i, (interface, ranges) in enumerate(network_ranges.items()):
            for j, range in enumerate(ranges):
                print(f"{i+j+1}. Interface: {interface}, Range: {range}")

        while True:
            try:
                choice = int(input("Select a network range to scan (enter the number): "))
                selected_range = list(network_ranges.values())[choice-1][0]
                break
            except (ValueError, IndexError):
                print("Invalid choice. Please enter a valid number.")

        print(f"Scanning network range: {selected_range}")
        online_devices = scan_network(selected_range)
        display_scan_results(online_devices)
    else:
        print("Could not determine network ranges.")
