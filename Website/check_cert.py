import os
import ssl

def check_certificate():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ca_path = os.path.join(current_dir, 'Backend', 'ca.pem')
    
    print("Certificate Check Utility")
    print("-----------------------")
    
    # Check if certificate exists
    if not os.path.exists(ca_path):
        print(f"❌ Certificate not found at: {ca_path}")
        return False
    
    print(f"✓ Certificate found at: {ca_path}")
    
    # Try to load certificate
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cafile=ca_path)
        print("✓ Certificate loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Error loading certificate: {e}")
        return False

if __name__ == "__main__":
    check_certificate() 