#!/usr/bin/env python3
"""
Combined Barcode Scanner with HTTPS Support and Testing
A Flask-based barcode scanner with automatic HTTPS setup and connectivity testing
"""

import sys
import argparse
from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
import json
from datetime import datetime
import socket
import ssl
import ipaddress
from werkzeug.serving import WSGIRequestHandler

# Testing imports
import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)


# ============================================================================
# HTTPS CERTIFICATE FUNCTIONS
# ============================================================================

def create_self_signed_cert():
    """Create a self-signed certificate for HTTPS"""
    try:
        import ssl
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime

        # Remove old certificates to force regeneration
        for cert_file in ['cert.pem', 'key.pem']:
            if os.path.exists(cert_file):
                try:
                    os.remove(cert_file)
                    print(f"🔄 Removed old {cert_file}")
                except:
                    pass

        print("🔧 Generating new HTTPS certificates...")

        # Generate private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Local"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Barcode Scanner"),
            x509.NameAttribute(NameOID.COMMON_NAME, get_local_ip()),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.DNSName(u"127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address(get_local_ip())),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(key, hashes.SHA256())

        # Write certificate and key to files
        with open("cert.pem", "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open("key.pem", "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        print("✅ HTTPS certificates created successfully")
        print(f"📄 Certificate includes IPs: 127.0.0.1, {get_local_ip()}")
        return True
    except ImportError:
        print("⚠️  cryptography library not found. Install with: pip install cryptography")
        return False
    except Exception as e:
        print(f"⚠️  Certificate creation failed: {e}")
        return False


def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_access_urls(use_https=False):
    """Generate access URLs for web and mobile"""
    local_ip = get_local_ip()
    port = 5000
    protocol = "https" if use_https else "http"

    return {
        'localhost': f'{protocol}://localhost:{port}',
        'network': f'{protocol}://{local_ip}:{port}',
        'local_ip': local_ip,
        'protocol': protocol
    }


def check_firewall_and_network():
    """Check if network access might be blocked"""
    try:
        # Try to bind to the network interface
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('0.0.0.0', 0))  # Bind to any available port
        test_socket.close()
        return True
    except Exception as e:
        print(f"⚠️  Network binding test failed: {e}")
        return False


# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def get_product_by_barcode(barcode_value):
    """Get product information from database by barcode"""
    try:
        conn = sqlite3.connect("testing_system.db")
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.product_id,
                   p.product_name,
                   COALESCE(p.product_desc, p.description, '') AS product_desc,
                   p.manufacture_date,
                   p.expired_date,
                   p.arrival_date,
                   p.location,
                   p.batch,
                   p.barcode,
                   p.sku,
                   p.product_image,
                   p.status,
                   p.branch_id,
                   COALESCE(u.username, 'Unknown') AS username
            FROM products p
            LEFT JOIN users u ON u.user_id = COALESCE(p.user_id, p.owner_id)
            WHERE p.barcode = ?
              AND LOWER(p.status) = 'approved'
        """, (barcode_value,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'product_id': result['product_id'],
                'product_name': result['product_name'],
                'description': result['product_desc'],
                'manufacture_date': result['manufacture_date'],
                'expired_date': result['expired_date'],
                'arrival_date': result['arrival_date'],
                'location': result['location'],
                'batch': result['batch'],
                'barcode': result['barcode'],
                'sku': result['sku'],
                'product_image': result['product_image'],
                'status': result['status'],
                'branch': result['branch_id'],
                'owner': result['username']
            }
        return None
    except Exception as e:
        # Log detailed error for debugging
        print(f"Database error in get_product_by_barcode: {e}")
        return None


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main page with barcode scanner"""
    use_https = request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'
    urls = get_access_urls(use_https)
    return render_template('scanner.html', urls=urls)


@app.route('/links')
def access_links():
    """Display access links"""
    use_https = request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'
    urls = get_access_urls(use_https)
    return render_template('access_links.html', urls=urls)


@app.route('/scan', methods=['POST'])
def scan_barcode():
    """Handle barcode scan result"""
    data = request.get_json()
    barcode_value = data.get('barcode')

    if not barcode_value:
        return jsonify({'error': 'No barcode provided'}), 400

    # Get product information
    product = get_product_by_barcode(barcode_value)

    if product:
        return jsonify({
            'success': True,
            'product': product
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Product not found or not approved'
        }), 404


@app.route('/product/<barcode>')
def product_detail(barcode):
    """Display detailed product information"""
    product = get_product_by_barcode(barcode)

    if product:
        return render_template('product_detail.html', product=product)
    else:
        return render_template('not_found.html'), 404


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve product images"""
    # Get the directory containing the image
    image_dir = os.path.dirname(filename)
    image_name = os.path.basename(filename)

    # Try to serve from absolute path directory
    if os.path.exists(filename):
        return send_from_directory(image_dir, image_name)

    # Fallback: try to serve from current directory
    return send_from_directory('.', filename)


@app.route('/test')
def run_connectivity_test():
    """Run HTTPS connectivity test via web interface"""
    test_results = run_https_test()
    return jsonify(test_results)


# ============================================================================
# HTTPS TESTING FUNCTIONS
# ============================================================================

def test_ssl_socket(host, port):
    """Test SSL socket connection"""
    try:
        print(f"🔍 Testing SSL socket connection to {host}:{port}...")

        # Create SSL context that accepts self-signed certificates
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA')

        # Test connection with very short timeout for Flask dev server
        with socket.create_connection((host, port), timeout=1) as sock:
            sock.settimeout(1)  # Very short SSL handshake timeout
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"✅ SSL connection successful!")
                cert = ssock.getpeercert()
                if cert:
                    print(f"📄 Certificate subject: {cert.get('subject', 'Unknown')}")
                return True

    except (socket.timeout, ssl.SSLError) as e:
        print(f"⚠️  SSL handshake timeout (normal for Flask dev server)")
        print("   This is expected behavior - Flask dev server has SSL limitations")
        return False
    except Exception as e:
        print(f"❌ SSL connection failed: {e}")
        return False


def test_https_request(url):
    """Test HTTPS request"""
    try:
        print(f"🌐 Testing HTTPS request to {url}...")

        # Configure session with better SSL handling
        session = requests.Session()
        session.verify = False

        # Add headers that Flask expects
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        response = session.get(url, headers=headers, timeout=5, allow_redirects=True)

        if response.status_code == 200:
            print(f"✅ HTTPS request successful! Status: {response.status_code}")
            print(f"📄 Content length: {len(response.content)} bytes")
            return True
        else:
            print(f"⚠️  HTTPS request returned status: {response.status_code}")
            return False

    except requests.exceptions.Timeout as e:
        print(f"⚠️  HTTPS request timeout (server may be running HTTP instead of HTTPS)")
        print("   Try testing the HTTP version or check server startup logs")
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


def run_https_test():
    """Run complete HTTPS connectivity test"""
    print("=" * 60)
    print("🔒 HTTPS CONNECTIVITY TEST")
    print("=" * 60)

    local_ip = get_local_ip()

    print(f"📍 Local IP: {local_ip}")
    print(f"🔗 Testing URLs:")
    print(f"   • https://localhost:5000")
    print(f"   • https://{local_ip}:5000")

    # Check if certificates exist
    cert_exists = os.path.exists('cert.pem') and os.path.exists('key.pem')
    print(f"🔐 SSL Certificates: {'✅ Found' if cert_exists else '❌ Missing'}")

    if not cert_exists:
        print("🔧 Creating SSL certificates...")
        cert_created = create_self_signed_cert()
        if not cert_created:
            print("❌ Cannot create certificates - cryptography library missing")
            print("   Install with: pip install cryptography")
            return {'success': False, 'error': 'certificates_missing'}

    print()

    # Test localhost
    print("🏠 LOCALHOST TESTS:")
    print("-" * 30)
    localhost_port_ok = test_port_accessibility("127.0.0.1", 5000)
    localhost_ssl_ok = test_ssl_socket("127.0.0.1", 5000) if localhost_port_ok else False
    localhost_https_ok = test_https_request("https://localhost:5000") if localhost_port_ok else False

    # Test if server is running HTTP instead of HTTPS
    localhost_http_ok = False
    if localhost_port_ok and not localhost_https_ok:
        print("🔍 Testing if server is running HTTP instead of HTTPS...")
        try:
            response = requests.get("http://localhost:5000", timeout=3)
            if response.status_code == 200:
                localhost_http_ok = True
                print("⚠️  Server is running HTTP instead of HTTPS!")
        except:
            pass

    print()

    # Test network IP
    print("🌐 NETWORK TESTS:")
    print("-" * 30)
    network_port_ok = test_port_accessibility(local_ip, 5000)
    network_ssl_ok = test_ssl_socket(local_ip, 5000) if network_port_ok else False
    network_https_ok = test_https_request(f"https://{local_ip}:5000") if network_port_ok else False

    # Test if server is running HTTP instead of HTTPS on network
    network_http_ok = False
    if network_port_ok and not network_https_ok:
        print("🔍 Testing if network server is running HTTP instead of HTTPS...")
        try:
            response = requests.get(f"http://{local_ip}:5000", timeout=3)
            if response.status_code == 200:
                network_http_ok = True
                print("⚠️  Network server is running HTTP instead of HTTPS!")
        except:
            pass

    print()
    print("=" * 60)
    print("📊 RESULTS SUMMARY:")
    print("=" * 60)

    print(f"🏠 Localhost (https://localhost:5000):")
    print(f"   Port accessible: {'✅' if localhost_port_ok else '❌'}")
    print(f"   SSL working: {'✅' if localhost_ssl_ok else '❌'}")
    print(f"   HTTPS working: {'✅' if localhost_https_ok else '❌'}")
    print(f"   HTTP working: {'✅' if localhost_http_ok else '❌'}")

    print(f"🌐 Network (https://{local_ip}:5000):")
    print(f"   Port accessible: {'✅' if network_port_ok else '❌'}")
    print(f"   SSL working: {'✅' if network_ssl_ok else '❌'}")
    print(f"   HTTPS working: {'✅' if network_https_ok else '❌'}")
    print(f"   HTTP working: {'✅' if network_http_ok else '❌'}")

    print()

    if localhost_https_ok and network_https_ok:
        print("🎉 ALL TESTS PASSED!")
        print("Your HTTPS server is working correctly.")
        success = True
    elif localhost_http_ok or network_http_ok:
        print("⚠️  SERVER RUNNING HTTP INSTEAD OF HTTPS!")
        print("The server started but fell back to HTTP mode.")
        print("📱 Mobile camera scanning will NOT work without HTTPS!")
        print("💡 Check server startup logs for SSL certificate errors.")
        success = False
    elif localhost_https_ok:
        print("⚠️  PARTIAL SUCCESS:")
        print("Localhost works, but network access has issues.")
        print("This is likely a firewall or network configuration problem.")
        success = False
    else:
        print("❌ TESTS FAILED:")
        print("HTTPS server is not working properly.")
        success = False

    print("\n🛠️  TROUBLESHOOTING:")
    if not localhost_port_ok and not network_port_ok:
        print("• ❌ SERVER NOT RUNNING - Start with: python combined_scanner.py --server")
        print("• The connectivity test requires the server to be running first!")
    elif not localhost_port_ok:
        print("• ❌ Localhost not accessible - Server may not be running")
    elif not network_port_ok:
        print("• ❌ Network access blocked - Run fix_firewall.bat as Administrator")
        print("• Windows Firewall is likely blocking port 5000")

    if localhost_http_ok or network_http_ok:
        print("• ⚠️  SERVER RUNNING HTTP INSTEAD OF HTTPS!")
        print("  - Check server startup logs for SSL certificate errors")
        print(
            "  - Recreate certificates: python -c \"from combined_scanner import create_self_signed_cert; create_self_signed_cert()\"")
        print("  - Mobile camera scanning will NOT work with HTTP only")
    elif localhost_port_ok and not localhost_https_ok:
        print("• ⚠️  HTTPS request failed - Check SSL configuration")
    if network_port_ok and not network_https_ok and not network_http_ok:
        print("• ⚠️  Network HTTPS failed - Firewall or antivirus blocking SSL")

    if localhost_port_ok or network_port_ok:
        print("\n💡 TIPS:")
        print("• SSL socket timeouts are NORMAL with Flask development server")
        print("• HTTPS requests working = SSL is actually functional")
        print("• Test in browser: https://localhost:5000 or https://192.168.188.176:5000")
        print("• Accept the security warning for self-signed certificates")
        print("• For mobile: HTTPS is REQUIRED for camera access!")

    return {
        'local_ip': local_ip,
        'localhost': {
            'port_ok': localhost_port_ok,
            'ssl_ok': localhost_ssl_ok,
            'https_ok': localhost_https_ok,
            'http_ok': localhost_http_ok
        },
        'network': {
            'port_ok': network_port_ok,
            'ssl_ok': network_ssl_ok,
            'https_ok': network_https_ok,
            'http_ok': network_http_ok
        },
        'success': success,
        'server_mode': 'https' if localhost_https_ok or network_https_ok else 'http' if localhost_http_ok or network_http_ok else 'none'
    }


# ============================================================================
# SERVER FUNCTIONS
# ============================================================================

def run_flask_server():
    """Run the Flask barcode scanner server"""
    # Check network access
    network_ok = check_firewall_and_network()

    # Try to create HTTPS certificates
    https_available = create_self_signed_cert()

    # Determine whether to use HTTPS
    use_https = https_available and os.path.exists('cert.pem') and os.path.exists('key.pem')

    # Get network information
    urls_http = get_access_urls(False)
    urls_https = get_access_urls(True) if use_https else None

    print("\n" + "=" * 70)
    print("🔗 COMBINED BARCODE SCANNER - SERVER MODE")
    print("=" * 70)

    if use_https:
        print("🔒 HTTPS ENABLED - Camera will work on mobile!")
        print(f"📱 Local Access (HTTPS):  {urls_https['localhost']}")
        print(f"🌐 Network Access (HTTPS): {urls_https['network']}")
        print(f"📱 Local Access (HTTP):   {urls_http['localhost']}")
        print(f"🌐 Network Access (HTTP):  {urls_http['network']}")
    else:
        print("⚠️  HTTP ONLY - Mobile camera may not work")
        print(f"📱 Local Access:     {urls_http['localhost']}")
        print(f"🌐 Network Access:   {urls_http['network']}")

    print(f"📍 Local IP:         {urls_http['local_ip']}")
    print("=" * 70)

    if not network_ok:
        print("⚠️  NETWORK WARNING:")
        print("   Network access may be blocked by firewall")
        print("   Windows Firewall might be blocking port 5000")
        print("=" * 70)

    print("📱 For mobile access:")
    print("   1. Connect phone to same WiFi network")

    if use_https:
        print(f"   2. Open browser and go to: {urls_https['network']}")
        print("   3. Accept the security warning (self-signed certificate)")
        print("   4. Camera should work on mobile!")
    else:
        print(f"   2. Open browser and go to: {urls_http['network']}")
        print("   3. Camera may not work - use manual entry")
        print("   4. Install cryptography for HTTPS: pip install cryptography")

    print("=" * 70)
    print("🚀 Server starting...")
    print("=" * 70)

    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    # Try to run with HTTPS, fallback to HTTP if needed
    try:
        if use_https:
            print("🔐 Attempting to start HTTPS server...")

            # Configure SSL context with better compatibility
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain('cert.pem', 'key.pem')
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Set minimum and maximum TLS versions for better compatibility
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

            # Enable broader cipher support for better client compatibility
            ssl_context.set_ciphers(
                'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:ECDHE+AES256:ECDHE+AES128:DHE+AES256:DHE+AES128:AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256:AES256-SHA:AES128-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA')

            # Disable SSL compression to prevent CRIME attacks
            ssl_context.options |= ssl.OP_NO_COMPRESSION

            app.run(host='0.0.0.0', port=5000, debug=False, ssl_context=ssl_context, threaded=True)
        else:
            print("🌐 Starting HTTP server...")
            print("⚠️  WARNING: Mobile camera scanning will NOT work without HTTPS!")
            app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

    except ssl.SSLError as e:
        print(f"\n⚠️  HTTPS Failed: {e}")
        print("🔄 Falling back to HTTP server...")
        print("📱 WARNING: Mobile camera scanning will NOT work without HTTPS!")
        print("💡 SSL Certificate issue - check cert.pem and key.pem files")

        # Fallback to HTTP
        try:
            app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        except Exception as fallback_error:
            print(f"❌ HTTP fallback also failed: {fallback_error}")

    except OSError as e:
        if "WinError 10013" in str(e) or "Permission denied" in str(e):
            print("\n❌ PORT 5000 ACCESS DENIED!")
            print("This is likely due to Windows Firewall or another app using port 5000")
            print("\n🛠️  SOLUTIONS:")
            print("1. Run as Administrator")
            print("2. Allow Python through Windows Firewall")
            print("3. Run fix_firewall.bat as Administrator")
            print("4. Try different port (edit the code to use port 5000)")
            print("5. Check if IIS or other service is using port 5000")
            print("\n🔧 NETWORK TROUBLESHOOTING:")
            print(f"• Test local: curl -k https://localhost:5000")
            print(f"• Test network: curl -k https://{get_local_ip()}:5000")
        else:
            print(f"\n❌ Server startup failed: {e}")
            print("Try running as Administrator or changing the port number")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("🔄 Trying HTTP fallback...")
        try:
            app.run(host='0.0.0.0', port=5000, debug=True)
        except Exception as fallback_error:
            print(f"❌ HTTP fallback also failed: {fallback_error}")


# ============================================================================
# MAIN FUNCTION AND CLI
# ============================================================================

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Combined Barcode Scanner with HTTPS Support and Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python combined_scanner.py --server          # Run Flask server
  python combined_scanner.py --test            # Run connectivity test
  python combined_scanner.py --interactive     # Interactive menu
  python combined_scanner.py                   # Interactive menu (default)
        """
    )

    parser.add_argument('--server', '-s', action='store_true',
                        help='Start the Flask barcode scanner server')
    parser.add_argument('--test', '-t', action='store_true',
                        help='Run HTTPS connectivity test')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Show interactive menu')

    args = parser.parse_args()

    # If no arguments provided, show interactive menu
    if not any([args.server, args.test, args.interactive]):
        args.interactive = True

    if args.server:
        print("🚀 Starting Flask Barcode Scanner Server...")
        run_flask_server()

    elif args.test:
        print("🔍 Running HTTPS Connectivity Test...")
        result = run_https_test()
        return 0 if result['success'] else 1

    elif args.interactive:
        print("=" * 60)
        print("🔗 COMBINED BARCODE SCANNER")
        print("=" * 60)
        print("Choose an option:")
        print("1. 🚀 Start Flask Server (Barcode Scanner)")
        print("2. 🔍 Run HTTPS Connectivity Test")
        print("3. 📄 Show Access URLs")
        print("4. ❌ Exit")
        print()

        while True:
            try:
                choice = input("Enter your choice (1-4): ").strip()

                if choice == '1':
                    print("\n🚀 Starting Flask Barcode Scanner Server...")
                    run_flask_server()
                    break

                elif choice == '2':
                    print("\n🔍 Running HTTPS Connectivity Test...")
                    result = run_https_test()
                    print(f"\nTest completed. Success: {'Yes' if result['success'] else 'No'}")
                    print("\nPress Enter to continue...")
                    input()

                elif choice == '3':
                    print("\n📄 Current Access URLs:")
                    local_ip = get_local_ip()
                    print(f"📍 Local IP: {local_ip}")
                    print(f"🏠 Local Access:  http://localhost:5000")
                    print(f"🌐 Network Access: http://{local_ip}:5000")
                    print(f"🔒 HTTPS Local:   https://localhost:5000")
                    print(f"🔒 HTTPS Network: https://{local_ip}:5000")
                    print("\nPress Enter to continue...")
                    input()

                elif choice == '4':
                    print("👋 Goodbye!")
                    break

                else:
                    print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)