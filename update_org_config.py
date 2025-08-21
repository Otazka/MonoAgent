#!/usr/bin/env python3
"""
Update organization configuration in .env.

Usage: python update_org_config.py <new_org>
If no argument is provided, prints current ORG value.
"""

def update_org_config():
    """Update the .env file to use the provided organization."""
    import sys
    import os

    if not os.path.exists('.env'):
        print("❌ .env file not found. Copy env.example to .env first.")
        return

    new_org = sys.argv[1] if len(sys.argv) > 1 else None
    with open('.env', 'r') as f:
        content = f.read()

    current = None
    for line in content.splitlines():
        if line.startswith('ORG='):
            current = line.split('=', 1)[1]
            break

    if not new_org:
        print(f"Current ORG: {current or 'NOT SET'}")
        print("Provide new org as an argument to update: python update_org_config.py my-org")
        return

    updated = []
    found = False
    for line in content.splitlines():
        if line.startswith('ORG='):
            updated.append(f"ORG={new_org}")
            found = True
        else:
            updated.append(line)

    if not found:
        updated.append(f"ORG={new_org}")

    with open('.env', 'w') as f:
        f.write("\n".join(updated) + "\n")

    print(f"✅ Updated .env to use ORG={new_org}")
    print("Now you can run the force update script to populate the repositories")

if __name__ == "__main__":
    update_org_config()
