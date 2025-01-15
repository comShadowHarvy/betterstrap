import nmap
import datetime

# Define the subnet or IP range
subnet = '192.168.1.0/24'

# Initialize the nmap scanner
nm = nmap.PortScanner()

# Run the scan
nm.scan(subnet, arguments='-sV')

# Define the output file
output_file = '/path/to/output_file.txt'

# Write scan results to file
with open(output_file, 'a') as f:
    f.write(f"Scan completed at {datetime.datetime.now()}\n")
    for host in nm.all_hosts():
        f.write(f"Host: {host} ({nm[host].hostname()})\n")
        f.write(f"State: {nm[host].state()}\n")
        for proto in nm[host].all_protocols():
            f.write(f"Protocol: {proto}\n")
            lport = nm[host][proto].keys()
            for port in lport:
                f.write(f"Port: {port}\tState: {nm[host][proto][port]['state']}\n")
    f.write("\n")

print("Scan completed and results saved.")
