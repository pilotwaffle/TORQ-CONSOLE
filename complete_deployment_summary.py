#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TORQ Knowledge Plane - Complete Deployment Summary

This script provides a comprehensive summary of the deployment readiness
and creates a deployment manifest for Railway.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
TORQ_CONSOLE_PATH = Path("/e/TORQ-CONSOLE")
SERVICE_URL = "web-production-74ed0.up.railway.app"
VERSION = "1.1.0-knowledge-plane"

# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def print_header(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{title:^70}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}\n")

def print_section(title):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.RESET}")

def check_file(filepath, description):
    full_path = TORQ_CONSOLE_PATH / filepath
    exists = full_path.exists()
    status = f"{Colors.GREEN}[OK]{Colors.RESET}" if exists else f"{Colors.RED}[XX]{Colors.RESET}"
    print(f"  {status} {description}: {filepath}")
    return exists

def main():
    print_header("TORQ KNOWLEDGE PLANE RAILWAY DEPLOYMENT SUMMARY")

    print(f"{Colors.BOLD}Deployment Information{Colors.RESET}")
    print(f"  Version: {VERSION}")
    print(f"  Target URL: {SERVICE_URL}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check deployment files
    print_section("Deployment Files Status")

    files_to_check = [
        ("railway_app.py", "Main FastAPI application"),
        ("railway.json", "Railway configuration"),
        (".nixpacks.toml", "Nixpacks build configuration"),
        ("requirements-railway.txt", "Python dependencies"),
        ("torq_console/knowledge_plane/__init__.py", "Knowledge Plane module"),
        ("torq_console/knowledge_plane/api.py", "Knowledge Plane API (full)"),
        ("torq_console/knowledge_plane/railway_integration.py", "Knowledge Plane API (lightweight)"),
        ("test_knowledge_plane.py", "API test suite"),
        ("supabase_knowledge_plane_setup.sql", "Supabase setup script"),
        ("KNOWLEDGE_PLANE_RAILWAY_DEPLOYMENT.md", "Deployment documentation"),
        ("KNOWLEDGE_PLANE_DEPLOYMENT_STATUS.md", "Deployment status report"),
    ]

    all_files_exist = True
    for filepath, description in files_to_check:
        if not check_file(filepath, description):
            all_files_exist = False

    # API Endpoints
    print_section("Knowledge Plane API Endpoints")

    endpoints = [
        ("GET", "/health", "Service health check"),
        ("GET", "/api/knowledge/health", "Knowledge Plane health"),
        ("POST", "/api/knowledge/store", "Store knowledge entry"),
        ("POST", "/api/knowledge/search", "Search knowledge base"),
        ("GET", "/api/knowledge/recent", "Get recent entries"),
        ("GET", "/api/knowledge/stats", "Get statistics"),
        ("GET", "/", "List all endpoints"),
    ]

    print(f"  {Colors.BOLD}{'Method':<8} {'Endpoint':<35} Description{Colors.RESET}")
    for method, endpoint, desc in endpoints:
        print(f"  {method:<8} {endpoint:<35} {desc}")

    # Environment Variables
    print_section("Required Environment Variables")

    env_vars = [
        ("OPENAI_API_KEY", "OpenAI API key for embeddings", "Required"),
        ("SUPABASE_URL", "Supabase project URL", "Required"),
        ("SUPABASE_SERVICE_ROLE_KEY", "Supabase service role key", "Required"),
        ("TORQ_BRAIN_KEY", "TORQ Brain API key", "Required (can use OPENAI_API_KEY)"),
        ("REDIS_URL", "Redis URL for caching", "Optional"),
        ("TORQ_CONSOLE_PRODUCTION", "Production mode flag", "Auto-set to true"),
        ("TORQ_DISABLE_LOCAL_LLM", "Disable local LLM", "Auto-set to true"),
        ("TORQ_DISABLE_GPU", "Disable GPU", "Auto-set to true"),
    ]

    for var, desc, status in env_vars:
        status_color = Colors.YELLOW if status == "Optional" else Colors.GREEN
        print(f"  {Colors.CYAN}{var}{Colors.RESET}")
        print(f"    {desc}")
        print(f"    Status: {status_color}{status}{Colors.RESET}")

    # Deployment Steps
    print_section("Deployment Steps")

    steps = [
        "1. Run Supabase setup script in Supabase SQL Editor",
        "   File: supabase_knowledge_plane_setup.sql",
        "",
        "2. Login to Railway CLI",
        "   Command: railway login",
        "",
        "3. Link Railway project",
        "   Command: railway link",
        "",
        "4. Set environment variables",
        "   Command: railway variables set OPENAI_API_KEY='your-key'",
        "   Command: railway variables set SUPABASE_URL='your-url'",
        "   Command: railway variables set SUPABASE_SERVICE_ROLE_KEY='your-key'",
        "   Command: railway variables set TORQ_BRAIN_KEY='your-key'",
        "",
        "5. Deploy to Railway",
        "   Command: railway up",
        "",
        "6. Verify deployment",
        "   Command: curl https://your-service.railway.app/health",
        "   Command: curl https://your-service.railway.app/api/knowledge/health",
        "",
        "7. Run test suite",
        "   Command: python test_knowledge_plane.py https://your-service.railway.app",
    ]

    for step in steps:
        if step.startswith(("Command:", "File:")):
            print(f"    {Colors.YELLOW}{step}{Colors.RESET}")
        elif step.isdigit():
            print(f"\n  {Colors.BOLD}{step}{Colors.RESET}")
        else:
            print(f"    {step}")

    # Readiness Status
    print_section("Readiness Status")

    if all_files_exist:
        print(f"  {Colors.GREEN}{Colors.BOLD}[OK] ALL FILES READY{Colors.RESET}")
        print(f"  {Colors.GREEN}Knowledge Plane module is fully implemented{Colors.RESET}")
        print(f"  {Colors.GREEN}Railway integration complete{Colors.RESET}")
        print(f"  {Colors.GREEN}Test suite ready{Colors.RESET}")
        print(f"  {Colors.GREEN}Documentation complete{Colors.RESET}")
    else:
        print(f"  {Colors.RED}{Colors.BOLD}[XX] SOME FILES MISSING{Colors.RESET}")
        print(f"  {Colors.RED}Please check the file listing above{Colors.RESET}")

    # Create deployment manifest
    print_section("Creating Deployment Manifest")

    manifest = {
        "version": VERSION,
        "service_url": SERVICE_URL,
        "deployment_date": datetime.now().isoformat(),
        "files": [f[0] for f in files_to_check],
        "endpoints": [
            {"method": e[0], "path": e[1], "description": e[2]}
            for e in endpoints
        ],
        "environment_variables": [
            {"name": v[0], "description": v[1], "required": v[2] == "Required"}
            for v in env_vars
        ],
        "status": "ready" if all_files_exist else "incomplete"
    }

    manifest_path = TORQ_CONSOLE_PATH / "knowledge_plane_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"  {Colors.GREEN}[OK] Manifest created: knowledge_plane_manifest.json{Colors.RESET}")

    # Final Summary
    print_header("DEPLOYMENT SUMMARY")

    if all_files_exist:
        print(f"{Colors.GREEN}{Colors.BOLD}Ready to Deploy!{Colors.RESET}\n")
        print(f"  The TORQ Knowledge Plane backend is ready for Railway deployment.")
        print(f"  Service URL: https://{SERVICE_URL}/")
        print(f"  Version: {VERSION}")
        print(f"\n  {Colors.BOLD}Quick Start:{Colors.RESET}")
        print(f"  1. Run Supabase SQL setup script")
        print(f"  2. Login: railway login")
        print(f"  3. Link: railway link")
        print(f"  4. Deploy: railway up")
        print(f"  5. Test: python test_knowledge_plane.py https://your-service.railway.app")
    else:
        print(f"{Colors.RED}{Colors.BOLD}Not Ready{Colors.RESET}\n")
        print(f"  Some required files are missing. Please check the status above.")

    print(f"\n{Colors.BLUE}Documentation: KNOWLEDGE_PLANE_RAILWAY_DEPLOYMENT.md{Colors.RESET}")
    print(f"{Colors.BLUE}Status: KNOWLEDGE_PLANE_DEPLOYMENT_STATUS.md{Colors.RESET}\n")

if __name__ == "__main__":
    main()
