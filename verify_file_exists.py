#!/usr/bin/env python3
"""
Final verification that capabilities.yaml exists and has correct structure
"""
import yaml
import sys
from pathlib import Path

def main():
    print("=" * 70)
    print("CAPABILITIES.YAML FILE VERIFICATION")
    print("=" * 70)
    
    # Check file exists
    cap_file = Path("capabilities.yaml")
    if not cap_file.exists():
        print("❌ FAIL: capabilities.yaml does not exist!")
        return False
    
    print("✅ File exists: capabilities.yaml")
    print(f"   Size: {cap_file.stat().st_size} bytes")
    print()
    
    # Parse YAML
    try:
        with open(cap_file, 'r') as f:
            data = yaml.safe_load(f)
        print("✅ Valid YAML syntax")
    except Exception as e:
        print(f"❌ FAIL: Invalid YAML - {e}")
        return False
    
    # Verify structure
    print()
    print("STRUCTURE VERIFICATION:")
    print("-" * 70)
    
    # Check version
    if 'version' not in data:
        print("❌ Missing 'version' field")
        return False
    print(f"✅ version: {data['version']}")
    
    # Check personas
    if 'personas' not in data:
        print("❌ Missing 'personas' field")
        return False
    
    required_personas = ['basic_user', 'power_user']
    for persona in required_personas:
        if persona in data['personas']:
            desc = data['personas'][persona]['description']
            print(f"✅ persona '{persona}': {desc[:50]}...")
        else:
            print(f"❌ Missing persona: {persona}")
            return False
    
    # Check capabilities
    if 'capabilities' not in data:
        print("❌ Missing 'capabilities' field")
        return False
    
    print()
    print(f"CAPABILITIES VERIFICATION ({len(data['capabilities'])} total):")
    print("-" * 70)
    
    required_capabilities = [
        'cli_help', 'eval_help', 'bench_help', 'mcp_help',
        'config_init_help', 'serve_help', 'eval_requires_set',
        'mcp_requires_endpoint', 'sandbox_blocks_proc_mem',
        'sandbox_blocks_write_outside_workspace'
    ]
    
    actual_ids = [cap['id'] for cap in data['capabilities']]
    
    for cap_id in required_capabilities:
        if cap_id in actual_ids:
            cap = next(c for c in data['capabilities'] if c['id'] == cap_id)
            expect = cap['verify']['expect']
            print(f"✅ {cap_id:40s} expect: {expect}")
        else:
            print(f"❌ {cap_id:40s} MISSING")
            return False
    
    # Verify each capability has required fields
    print()
    print("CAPABILITY FIELD VERIFICATION:")
    print("-" * 70)
    
    required_fields = ['id', 'personas', 'description', 'dependencies', 'verify']
    verify_fields = ['command', 'expect', 'artifacts']
    
    all_valid = True
    for cap in data['capabilities']:
        cap_id = cap['id']
        
        # Check required fields
        missing_fields = [f for f in required_fields if f not in cap]
        if missing_fields:
            print(f"❌ {cap_id}: missing fields {missing_fields}")
            all_valid = False
            continue
            
        # Check verify section
        verify = cap['verify']
        missing_verify = [f for f in verify_fields if f not in verify]
        if missing_verify:
            print(f"❌ {cap_id}: missing verify fields {missing_verify}")
            all_valid = False
            continue
        
        print(f"✅ {cap_id}: all required fields present")
    
    if not all_valid:
        return False
    
    print()
    print("=" * 70)
    print("✅ ALL VERIFICATIONS PASSED")
    print("=" * 70)
    print()
    print("SUMMARY:")
    print(f"  • File: capabilities.yaml exists and is valid YAML")
    print(f"  • Version: {data['version']}")
    print(f"  • Personas: {len(data['personas'])} (basic_user, power_user)")
    print(f"  • Capabilities: {len(data['capabilities'])} defined")
    print(f"  • All required capabilities present")
    print(f"  • All capabilities have required fields")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
