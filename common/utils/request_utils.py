"""
Request utilities for extracting and validating client information
"""
import ipaddress
import re
from typing import Optional
from fastapi import Request


class IPValidationError(Exception):
    """Custom exception for IP validation errors"""
    pass


def extract_client_ip(request: Request) -> str:
    """
    Extract and validate client IP from request headers
    
    Args:
        request: FastAPI Request object
        
    Returns:
        str: Validated client IP address
        
    Raises:
        IPValidationError: If extracted IP is invalid
    """
    # List of headers to check in order of preference
    ip_headers = [
        'X-Forwarded-For',
        'X-Real-IP', 
        'CF-Connecting-IP',  # Cloudflare
        'True-Client-IP',    # Cloudflare
        'X-Client-IP',
        'X-Forwarded',
        'Forwarded-For',
        'Forwarded'
    ]
    
    # Check headers in order
    for header in ip_headers:
        ip_value = request.headers.get(header)
        if ip_value:
            # X-Forwarded-For can contain multiple IPs, get the first one
            if header.lower() in ['x-forwarded-for', 'forwarded-for', 'forwarded']:
                ip_value = ip_value.split(',')[0].strip()
            
            # Validate the IP
            if is_valid_ip(ip_value):
                return normalize_ip(ip_value)
    
    # Fallback to direct connection IP
    if request.client and request.client.host:
        direct_ip = request.client.host
        if is_valid_ip(direct_ip):
            return normalize_ip(direct_ip)
    
    # If no valid IP found, raise error
    raise IPValidationError("Unable to extract valid client IP from request")


def is_valid_ip(ip: str) -> bool:
    """
    Validate IP address format and check for private/reserved ranges
    
    Args:
        ip: IP address string to validate
        
    Returns:
        bool: True if IP is valid and acceptable
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        
        # Check for invalid or suspicious IPs
        if ip_obj.is_multicast:
            return False
        if ip_obj.is_reserved:
            return False
        if ip_obj.is_unspecified:
            return False
            
        # Allow private IPs for internal testing but log in production
        # if ip_obj.is_private:
        #     return False
            
        return True
        
    except ValueError:
        return False


def normalize_ip(ip: str) -> str:
    """
    Normalize IP address to standard format
    
    Args:
        ip: IP address string
        
    Returns:
        str: Normalized IP address
    """
    try:
        return str(ipaddress.ip_address(ip))
    except ValueError:
        raise IPValidationError(f"Invalid IP address format: {ip}")


def validate_ip_range(ip_range: str) -> bool:
    """
    Validate IP range in CIDR notation
    
    Args:
        ip_range: IP range string (e.g., "192.168.1.0/24")
        
    Returns:
        bool: True if IP range is valid
    """
    try:
        ipaddress.ip_network(ip_range, strict=False)
        return True
    except ValueError:
        return False


def get_ip_info(ip: str) -> dict:
    """
    Get information about an IP address
    
    Args:
        ip: IP address string
        
    Returns:
        dict: IP information including type, is_private, etc.
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        return {
            'ip': str(ip_obj),
            'version': ip_obj.version,
            'is_private': ip_obj.is_private,
            'is_loopback': ip_obj.is_loopback,
            'is_multicast': ip_obj.is_multicast,
            'is_reserved': ip_obj.is_reserved,
            'is_unspecified': ip_obj.is_unspecified,
            'is_global': ip_obj.is_global,
            'compressed': ip_obj.compressed if ip_obj.version == 6 else None,
            'exploded': ip_obj.exploded if ip_obj.version == 6 else None
        }
    except ValueError:
        raise IPValidationError(f"Invalid IP address: {ip}")


def is_ip_in_range(ip: str, ip_range: str) -> bool:
    """
    Check if IP address is within given range
    
    Args:
        ip: IP address to check
        ip_range: IP range in CIDR notation
        
    Returns:
        bool: True if IP is in range
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        network_obj = ipaddress.ip_network(ip_range, strict=False)
        return ip_obj in network_obj
    except ValueError:
        return False


def sanitize_forwarded_header(forwarded_value: str) -> str:
    """
    Sanitize and extract the first valid IP from Forwarded header
    
    Args:
        forwarded_value: Raw Forwarded header value
        
    Returns:
        str: Sanitized IP address or empty string
    """
    if not forwarded_value:
        return ""
    
    # Handle various Forwarded header formats
    # Format: "for=192.0.2.1;host=example.com;proto=https"
    parts = forwarded_value.split(';')
    for part in parts:
        part = part.strip()
        if part.startswith('for='):
            ip_part = part[4:].strip()
            # Remove quotes if present
            ip_part = ip_part.strip('"\'')
            # Remove port if present
            ip_part = re.sub(r':\d+$', '', ip_part)
            if is_valid_ip(ip_part):
                return normalize_ip(ip_part)
    
    return ""