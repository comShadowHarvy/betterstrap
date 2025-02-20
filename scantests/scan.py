import asyncio
import random
import socket
import struct
from typing import List, Tuple, Generator
from concurrent.futures import ThreadPoolExecutor
import ipaddress

def create_socket():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        s.settimeout(2.0)  # Add timeout
        return s
    except socket.error as e:
        print(f"Socket creation failed: {e}")
        exit()

# Pre-calculate random IPs for better performance
def generate_ip_pool(size: int = 100) -> List[str]:
    return [".".join(map(str, (random.randint(1, 255) for _ in range(4))))
            for _ in range(size)]

async def send_batch(sock: socket.socket, target_ip: str, 
                    ports: List[int], ip_pool: List[str]) -> None:
    for port in ports:
        try:
            spoofed_ip = random.choice(ip_pool)
            packet = create_syn_packet(spoofed_ip, target_ip, port)
            sock.sendto(packet, (target_ip, port))
            await asyncio.sleep(0.1)  # Reduced delay, using asyncio
        except Exception as e:
            print(f"Error scanning port {port}: {e}")

async def stealth_scan(target_ip: str, ports: List[int], 
                      batch_size: int = 50) -> None:
    sock = create_socket()
    ip_pool = generate_ip_pool()
    
    # Process ports in batches
    for i in range(0, len(ports), batch_size):
        batch = ports[i:i + batch_size]
        await send_batch(sock, target_ip, batch, ip_pool)

# Create a TCP SYN packet
def create_syn_packet(source_ip, dest_ip, dest_port):
    ip_header = struct.pack('!BBHHHBBH4s4s',
                            69, 0, 40, 54321, 0, 64, 6, 0,
                            socket.inet_aton(source_ip),
                            socket.inet_aton(dest_ip))

    tcp_header = struct.pack('!HHLLBBHHH',
                             random.randint(1024, 65535), dest_port, 0, 0,
                             5 << 4, 2, 1024, 0, 0)

    return ip_header + tcp_header

def get_ip_range(cidr: str) -> Generator[str, None, None]:
    """Generate all IP addresses in a CIDR range"""
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return (str(ip) for ip in network.hosts())
    except ValueError as e:
        print(f"Invalid CIDR notation: {e}")
        exit(1)

async def scan_network(cidr: str, ports: List[int], batch_size: int = 50) -> None:
    """Scan entire network range"""
    ip_pool = generate_ip_pool()
    for target_ip in get_ip_range(cidr):
        print(f"\nScanning host: {target_ip}")
        await stealth_scan(target_ip, ports, batch_size)
        await asyncio.sleep(0.5)  # Delay between hosts

# Example usage
if __name__ == "__main__":
    network = "192.168.1.0/24"  # Example CIDR notation
    ports_to_scan = [22, 80, 443, 8080]
    print(f"Scanning network: {network}")
    asyncio.run(scan_network(network, ports_to_scan))
