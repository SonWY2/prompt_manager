#!/usr/bin/env python3
"""
Script to clean up multiple default endpoints issue
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from gui.utils.db_client import DatabaseClient

def fix_default_endpoints():
    """Clean up multiple default endpoints - keep only one"""
    print("=== Fixing Multiple Default Endpoints ===\n")
    
    db_client = DatabaseClient()
    
    # Get all endpoints
    endpoints_data = db_client.get_llm_endpoints()
    endpoints = endpoints_data.get('endpoints', [])
    
    # Find all default endpoints
    default_endpoints = [ep for ep in endpoints if ep.get('isDefault', False)]
    
    print(f"Found {len(default_endpoints)} default endpoints:")
    for ep in default_endpoints:
        print(f"  - {ep['name']} (ID: {ep['id']})")
    
    if len(default_endpoints) > 1:
        print(f"\nFixing multiple defaults - keeping first one only...")
        
        # Keep first as default, unset others
        for i, ep in enumerate(default_endpoints):
            if i == 0:
                print(f"  Keeping as default: {ep['name']}")
            else:
                print(f"  Unsetting default: {ep['name']}")
                success = db_client.db.update_llm_endpoint(ep['id'], is_default=False)
                print(f"    Result: {'Success' if success else 'Failed'}")
    
    # Show final state
    print("\n=== Final State ===")
    final_data = db_client.get_llm_endpoints()
    active_id = final_data.get('activeEndpointId')
    default_id = final_data.get('defaultEndpointId')
    
    print(f"Active endpoint ID: {active_id}")
    print(f"Default endpoint ID: {default_id}")
    
    for ep in final_data.get('endpoints', []):
        is_active = ep['id'] == active_id
        is_default = ep.get('isDefault', False)
        status = []
        if is_active:
            status.append("ACTIVE")
        if is_default:
            status.append("DEFAULT")
        status_str = f" ({', '.join(status)})" if status else ""
        print(f"  - {ep['name']}: {ep['id']}{status_str}")
    
    print("\n=== Fix Complete ===")

if __name__ == "__main__":
    fix_default_endpoints()
