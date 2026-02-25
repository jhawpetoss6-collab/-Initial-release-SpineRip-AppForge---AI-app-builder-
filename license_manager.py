"""
SpineRip Trader - License Key Manager
Prevents unauthorized use of PRO features
"""

import os
import json
import hashlib
from datetime import datetime, timedelta


class LicenseManager:
    """Manage license keys and verification"""
    
    def __init__(self):
        self.license_file = os.path.join(os.path.dirname(__file__), '.license')
        self.master_key = "SPINERIP_MASTER_2026"  # Secret key for validation
    
    def generate_license_key(self, email, plan='monthly'):
        """Generate unique license key"""
        
        # Create unique hash from email + timestamp + master key
        timestamp = datetime.now().isoformat()
        raw = f"{email}{timestamp}{self.master_key}"
        hash_obj = hashlib.sha256(raw.encode())
        hash_hex = hash_obj.hexdigest()[:16].upper()
        
        # Format: SPINERIP-XXXX-XXXX-XXXX-XXXX
        key = f"SPINERIP-{hash_hex[0:4]}-{hash_hex[4:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}"
        
        # Save license
        expiration = None if plan == 'lifetime' else (datetime.now() + timedelta(days=30)).isoformat()
        
        license_data = {
            'key': key,
            'email': email,
            'plan': plan,
            'activated': datetime.now().isoformat(),
            'expiration': expiration,
            'status': 'active'
        }
        
        self.save_license(license_data)
        
        return key
    
    def save_license(self, license_data):
        """Save license to file"""
        with open(self.license_file, 'w') as f:
            json.dump(license_data, f, indent=2)
    
    def load_license(self):
        """Load license from file"""
        if not os.path.exists(self.license_file):
            return None
        
        try:
            with open(self.license_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def verify_license(self):
        """Verify if license is valid and active"""
        
        license_data = self.load_license()
        
        if not license_data:
            return False, "No license found. Please activate PRO subscription."
        
        # Check if expired
        if license_data.get('expiration'):
            expiration = datetime.fromisoformat(license_data['expiration'])
            if datetime.now() > expiration:
                return False, f"License expired on {expiration.strftime('%Y-%m-%d')}. Please renew."
        
        # Check if active
        if license_data.get('status') != 'active':
            return False, "License inactive. Please contact support."
        
        return True, f"✅ PRO Active - {license_data['plan'].title()} Plan"
    
    def activate_license(self, license_key, email):
        """Activate license with key"""
        
        # Validate key format
        if not license_key.startswith('SPINERIP-'):
            return False, "Invalid license key format"
        
        # In production, verify key with server
        # For now, save locally
        
        # Determine plan from key (you'd track this on your end)
        plan = 'monthly'  # Default
        
        license_data = {
            'key': license_key,
            'email': email,
            'plan': plan,
            'activated': datetime.now().isoformat(),
            'expiration': (datetime.now() + timedelta(days=30)).isoformat() if plan == 'monthly' else None,
            'status': 'active'
        }
        
        self.save_license(license_data)
        
        return True, "License activated successfully!"
    
    def deactivate_license(self):
        """Deactivate license (for testing)"""
        if os.path.exists(self.license_file):
            os.remove(self.license_file)
        return True
    
    def get_license_info(self):
        """Get current license information"""
        license_data = self.load_license()
        
        if not license_data:
            return {
                'status': 'inactive',
                'plan': 'free',
                'message': 'No active license'
            }
        
        valid, message = self.verify_license()
        
        return {
            'status': 'active' if valid else 'expired',
            'plan': license_data.get('plan', 'unknown'),
            'email': license_data.get('email'),
            'activated': license_data.get('activated'),
            'expiration': license_data.get('expiration'),
            'message': message
        }


def check_license_and_prompt():
    """Check license and prompt if needed"""
    
    manager = LicenseManager()
    valid, message = manager.verify_license()
    
    if not valid:
        print("\n" + "="*70)
        print("🔒 SPINERIP TRADER PRO - LICENSE REQUIRED")
        print("="*70 + "\n")
        print(f"❌ {message}\n")
        print("💰 Upgrade to PRO:")
        print("   • Monthly: $19/month")
        print("   • Lifetime: $99 one-time\n")
        print("💳 Payment: Cash App $JustinHawpetoss7")
        print("📧 Email: justinhawpetoss7@gmail.com\n")
        print("After payment, you'll receive a license key.")
        print("="*70 + "\n")
        
        # Ask if they have a key
        response = input("Do you have a license key? (y/n): ").strip().lower()
        
        if response == 'y':
            key = input("\nEnter your license key: ").strip()
            email = input("Enter your email: ").strip()
            
            success, msg = manager.activate_license(key, email)
            
            if success:
                print(f"\n✅ {msg}")
                print("🚀 You now have full PRO access!\n")
                return True
            else:
                print(f"\n❌ {msg}")
                print("Please contact support: justinhawpetoss7@gmail.com\n")
                return False
        else:
            print("\n👉 Visit: https://github.com/YOURUSERNAME/spinerip-trader")
            print("   Or pay via Cash App: $JustinHawpetoss7\n")
            return False
    
    print(f"\n✅ {message}\n")
    return True


# Command line tool
if __name__ == "__main__":
    import sys
    
    manager = LicenseManager()
    
    print("\n" + "="*70)
    print("🔑 SPINERIP TRADER - LICENSE MANAGER")
    print("="*70 + "\n")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'generate':
            # Generate new key
            email = input("Enter email: ").strip()
            plan = input("Plan (monthly/lifetime): ").strip().lower()
            
            if plan not in ['monthly', 'lifetime']:
                print("❌ Invalid plan. Use 'monthly' or 'lifetime'")
                sys.exit(1)
            
            key = manager.generate_license_key(email, plan)
            
            print(f"\n✅ License Key Generated!\n")
            print(f"📧 Email: {email}")
            print(f"💎 Plan: {plan.title()}")
            print(f"🔑 Key: {key}\n")
            print("Send this key to the customer!")
            print("="*70 + "\n")
        
        elif command == 'activate':
            # Activate license
            if len(sys.argv) < 4:
                print("Usage: python license_manager.py activate <key> <email>")
                sys.exit(1)
            
            key = sys.argv[2]
            email = sys.argv[3]
            
            success, message = manager.activate_license(key, email)
            print(f"\n{message}\n")
        
        elif command == 'info':
            # Show license info
            info = manager.get_license_info()
            
            print(f"Status: {info['status'].upper()}")
            print(f"Plan: {info['plan'].title()}")
            
            if info.get('email'):
                print(f"Email: {info['email']}")
            if info.get('activated'):
                print(f"Activated: {info['activated']}")
            if info.get('expiration'):
                print(f"Expires: {info['expiration']}")
            
            print(f"\n{info['message']}\n")
        
        elif command == 'deactivate':
            # Deactivate license
            manager.deactivate_license()
            print("✅ License deactivated\n")
        
        else:
            print(f"❌ Unknown command: {command}\n")
            print("Available commands:")
            print("  generate   - Generate new license key")
            print("  activate   - Activate license with key")
            print("  info       - Show current license info")
            print("  deactivate - Remove license (testing)\n")
    
    else:
        # Show current status
        check_license_and_prompt()
