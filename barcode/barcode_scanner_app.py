from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
import json
from datetime import datetime
import socket
import ssl
import ipaddress
from werkzeug.serving import WSGIRequestHandler

app = Flask(__name__)

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

def get_product_by_barcode(barcode_value):
    """Get product information from database by barcode"""
    try:
        conn = sqlite3.connect("medical_system.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.description, p.manufacture_date, 
                   p.expired_date, p.arrival_date, p.location, p.batch, p.barcode, 
                   p.sku, p.product_image, p.status, u.branch, u.username
            FROM Products p
            JOIN Users u ON p.user_id = u.user_id
            WHERE p.barcode = ? AND p.status = 'approved'
        """, (barcode_value,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'product_id': result[0],
                'product_name': result[1],
                'description': result[2],
                'manufacture_date': result[3],
                'expired_date': result[4],
                'arrival_date': result[5],
                'location': result[6],
                'batch': result[7],
                'barcode': result[8],
                'sku': result[9],
                'product_image': result[10],
                'status': result[11],
                'branch': result[12],
                'owner': result[13]
            }
        return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

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

if __name__ == '__main__':
    # Check network access
    network_ok = check_firewall_and_network()
    
    # Try to create HTTPS certificates
    https_available = create_self_signed_cert()
    
    # Determine whether to use HTTPS
    use_https = https_available and os.path.exists('cert.pem') and os.path.exists('key.pem')
    
    # Get network information
    urls_http = get_access_urls(False)
    urls_https = get_access_urls(True) if use_https else None
    
    print("\n" + "="*70)
    print("🔗 BARCODE SCANNER ACCESS LINKS")
    print("="*70)
    
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
    print("="*70)
    
    if not network_ok:
        print("⚠️  NETWORK WARNING:")
        print("   Network access may be blocked by firewall")
        print("   Windows Firewall might be blocking port 5000")
        print("="*70)
    
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
    
    print("="*70)
    
    if not network_ok:
        print("🛠️  TROUBLESHOOTING NETWORK ACCESS:")
        print("   • Windows: Allow Python through Windows Firewall")
        print("   • Router: Check if device isolation is disabled")
        print("   • Antivirus: Allow Python network access")
        print("="*70)
    
    print("🚀 Server starting...")
    print("="*70)
    
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Try to run with HTTPS, fallback to HTTP if needed
    try:
        if use_https:
            print("🔐 Attempting to start HTTPS server...")
            
            # Configure SSL context
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain('cert.pem', 'key.pem')
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Enable insecure ciphers for self-signed certificates
            ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=ssl_context)
        else:
            print("🌐 Starting HTTP server...")
            app.run(host='0.0.0.0', port=5000, debug=True)
            
    except ssl.SSLError as e:
        print(f"\n⚠️  HTTPS Failed: {e}")
        print("🔄 Falling back to HTTP server...")
        print("📱 Note: Mobile camera may not work without HTTPS")
        
        # Fallback to HTTP
        try:
            app.run(host='0.0.0.0', port=5000, debug=True)
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
            print("4. Try different port (edit the code to use port 8080)")
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