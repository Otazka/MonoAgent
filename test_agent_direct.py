#!/usr/bin/env python3
"""
Direct test of the RepoSplitter class
"""

import sys
import traceback
from split_repo_agent import RepoSplitter, RepoSplitterConfig

def test_direct():
    """Test the RepoSplitter directly."""
    print("🔍 Testing RepoSplitter directly...")
    
    try:
        # Create config
        config = RepoSplitterConfig(
            source_repo_url='',  # Will be loaded from .env
            branches=[],
            common_path=None,
            org='',
            github_token='',
            dry_run=True
        )
        
        print("✅ Config created")
        
        # Create splitter
        splitter = RepoSplitter(config)
        print("✅ RepoSplitter created")
        
        # Load config
        loaded_config = splitter.load_config()
        print(f"✅ Config loaded: {len(loaded_config.branches)} branches")
        
        # Test split repositories
        splitter.split_repositories()
        print("✅ split_repositories completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_direct()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
