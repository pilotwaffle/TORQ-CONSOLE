#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from supabase import create_client
from torq_console.settings import get_settings

client = create_client(get_settings().supabase.url, get_settings().supabase.service_role_key)
nodes = client.table('mission_nodes').select('*').eq('mission_id', '5be233f2-632c-4b2c-8a47-cb1c2c69a762').execute()

for n in nodes.data:
    print(f"{n['status']:12} | {n['node_type']:12} | {n['title']}")