#!/usr/bin/env python3
"""
HTTPS Connectivity Test Script
Test if the barcode scanner HTTPS server is accessible
"""

import requests
import urllib3
import socket
import ssl
import sys

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def test_ssl_socket(host, port):
    """Test SSL socket connection"""
    try:
        print(f"🔍 Testing SSL socket connection to {host}:{port}...")
        
        # Create SSL context that accepts self-signed certificates
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Test connection
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"✅ SSL connection successful!")
                cert = ssock.getpeercert()
                if cert:
                    print(f"📄 Certificate subject: {cert.get('subject', 'Unknown')}")
                return True
                
    except Exception as e:
        print(f"❌ SSL connection failed: {e}")
        return False

def test_https_request(url):
    """Test HTTPS request"""
    try:
        print(f"🌐 Testing HTTPS request to {url}...")
        
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ HTTPS request successful! Status: {response.status_code}")
            print(f"📄 Content length: {len(response.content)} bytes")
            return True
        else:
            print(f"⚠️  HTTPS request returned status: {response.status_code}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_port_accessibility(host, port):
    """Test if port is accessible"""
    try:
        print(f"🔌 Testing port accessibility {host}:{port}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is accessible on {host}")
            return True
        else:
            print(f"❌ Port {port} is not accessible on {host}")
            return False
            
    except Exception as e:
        print(f"❌ Port test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🔒 HTTPS CONNECTIVITY TEST")
    print("=" * 60)
    
    local_ip = get_local_ip()
    
    print(f"📍 Local IP: {local_ip}")
    print(f"🔗 Testing URLs:")
    print(f"   • https://localhost:5000")
    print(f"   • https://{local_ip}:5000")
    print()
    
    # Test localhost
    print("🏠 LOCALHOST TESTS:")
    print("-" * 30)
    localhost_port_ok = test_port_accessibility("127.0.0.1", 5000)
    localhost_ssl_ok = test_ssl_socket("127.0.0.1", 5000) if localhost_port_ok else False
    localhost_https_ok = test_https_request("https://localhost:5000") if localhost_ssl_ok else False
    
    print()
    
    # Test network IP
    print("🌐 NETWORK TESTS:")
    print("-" * 30)
    network_port_ok = test_port_accessibility(local_ip, 5000)
    network_ssl_ok = test_ssl_socket(local_ip, 5000) if network_port_ok else False
    network_https_ok = test_https_request(f"https://{local_ip}:5000") if network_ssl_ok else False
    
    print()
    print("=" * 60)
    print("📊 RESULTS SUMMARY:")
    print("=" * 60)
    
    print(f"🏠 Localhost (https://localhost:5000):")
    print(f"   Port accessible: {'✅' if localhost_port_ok else '❌'}")
    print(f"   SSL working: {'✅' if localhost_ssl_ok else '❌'}")
    print(f"   HTTPS working: {'✅' if localhost_https_ok else '❌'}")
    
    print(f"🌐 Network (https://{local_ip}:5000):")
    print(f"   Port accessible: {'✅' if network_port_ok else '❌'}")
    print(f"   SSL working: {'✅' if network_ssl_ok else '❌'}")
    print(f"   HTTPS working: {'✅' if network_https_ok else '❌'}")
    
    print()
    
    if localhost_https_ok and network_https_ok:
        print("🎉 ALL TESTS PASSED!")
        print("Your HTTPS server is working correctly.")
    elif localhost_https_ok:
        print("⚠️  PARTIAL SUCCESS:")
        print("Localhost works, but network access has issues.")
        print("This is likely a firewall or network configuration problem.")
    else:
        print("❌ TESTS FAILED:")
        print("HTTPS server is not working properly.")
        
    print("\n🛠️  TROUBLESHOOTING:")
    if not localhost_port_ok:
        print("• Server may not be running - start with: python barcode_scanner_app.py")
    if not network_port_ok:
        print("• Windows Firewall may be blocking - run fix_firewall.bat as Administrator")
    if localhost_port_ok and not localhost_ssl_ok:
        print("• SSL certificate issues - delete cert.pem and key.pem, restart server")
    if network_port_ok and not network_ssl_ok:
        print("• Network SSL issues - check if antivirus is blocking SSL connections")
        
    return 0 if (localhost_https_ok and network_https_ok) else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test script error: {e}")
        sys.exit(1) 