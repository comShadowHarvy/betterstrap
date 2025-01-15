#!/usr/bin/env python3

import os
import subprocess
import time
import socket
import ipaddress
from datetime import datetime
import xml.etree.ElementTree as ET

# Function to get the local IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Function to calculate the IP range
def get_ip_range(ip, subnet_mask='24'):
    network = ipaddress.IPv4Network(f'{ip}/{subnet_mask}', strict=False)
    return str(network)

# Function to run the Nmap scan
def run_nmap_scan(target):
    # Generate a timestamp for the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"nmap_scan_{target.replace('/', '_')}_{timestamp}.xml"
    
    # Build the Nmap command
    nmap_options = "-sS -sV -O -oX"  # TCP SYN scan, service version detection, OS detection, XML output
    nmap_command = f"nmap {nmap_options} {target} -oX {output_file}"
    
    # Execute the Nmap command
    print(f"Running Nmap scan on {target}...")
    print(f"Nmap command: {nmap_command}")  # Debugging output
    subprocess.run(nmap_command, shell=True)
    print(f"Scan completed. Results saved to {output_file}")
    
    return output_file

# Function to parse the Nmap results
def parse_nmap_results(nmap_output_file):
    tree = ET.parse(nmap_output_file)
    root = tree.getroot()
    
    high_priority_targets = []
    
    for host in root.findall('host'):
        ip_address = host.find('address').get('addr')
        for port in host.findall('ports/port'):
            port_id = port.get('portid')
            service = port.find('service')
            if service is not None:
                service_name = service.get('name')
                product = service.get('product', '')
                version = service.get('version', '')
                if service_name in ['http', 'ssh', 'smb', 'ftp']:
                    high_priority_targets.append((ip_address, port_id, service_name, product, version))
    
    return high_priority_targets

# Function to print high-priority targets
def print_high_priority_targets(targets):
    print("\nHigh-Priority Targets:")
    for target in targets:
        ip, port, service, product, version = target
        print(f"IP: {ip}, Port: {port}, Service: {service}, Product: {product}, Version: {version}")

# Function to run Nikto on high-priority HTTP targets
def run_nikto_scan(targets):
    for target in targets:
        ip, port, service, _, _ = target
        if service == 'http':
            output_file = f"nikto_scan_{ip}_{port}.txt"
            nikto_command = f"nikto -h {ip} -p {port} -o {output_file}"
            print(f"Running Nikto scan on {ip}:{port}...")
            subprocess.run(nikto_command, shell=True)
            print(f"Nikto scan completed. Results saved to {output_file}")

# Main function
def main():
    start_time = time.time()
    
    # Get the local IP and calculate the IP range
    local_ip = get_local_ip()
    ip_range = get_ip_range(local_ip)
    print(f"Detected IP range: {ip_range}")
    
    # Run the Nmap scan
    nmap_output_file = run_nmap_scan(ip_range)
    
    # Parse the Nmap results
    high_priority_targets = parse_nmap_results(nmap_output_file)
    
    # Print high-priority targets
    print_high_priority_targets(high_priority_targets)
    
    # Run Nikto scan on HTTP targets
    run_nikto_scan(high_priority_targets)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"All scans and analyses completed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()

