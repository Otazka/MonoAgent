#!/usr/bin/env python3
"""
Update organization configuration
"""

def update_org_config():
    """Update the .env file to use the correct organization."""
    
    # Read current .env
    with open('.env', 'r') as f:
        content = f.read()
    
    # Update ORG to Otazka
    content = content.replace('ORG=aiAgent', 'ORG=Otazka')
    
    # Write updated .env
    with open('.env', 'w') as f:
        f.write(content)
    
    print("✅ Updated .env to use ORG=Otazka")
    print("Now you can run the force update script to populate the repositories")

if __name__ == "__main__":
    update_org_config()
