from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
import json
from datetime import datetime

app = Flask(__name__)

def get_product_by_barcode(barcode_value):
    """Get product information from database by barcode"""
    try:
        conn = sqlite3.connect("testing_system.db")
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
    return render_template('scanner.html')

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
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Run the app on all interfaces so it can be accessed via IP
    app.run(host='0.0.0.0', port=5000, debug=True) 