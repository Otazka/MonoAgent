#!/usr/bin/env python3
"""
Wrapper script to run the AI agent with better error handling
"""

import sys
import traceback
from split_repo_agent import main

if __name__ == "__main__":
    try:
        print("🚀 Starting AI Agent...")
        main()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)
