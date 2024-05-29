import socket

def get_ip_address(dns_name):
    try:
        return socket.gethostbyname(dns_name)
    except socket.gaierror:
         return "Invalid DNS name"
    
def get_host_name(ip_address):
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except socket.gaierror:
           return "Invalid IP address"
