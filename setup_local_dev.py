#!/usr/bin/env python3
"""
Local Development Setup Script for StuckAI for Travel
This script helps set up the development environment for local PostgreSQL
"""

import os
import sys
import subprocess
from pathlib import Path

def check_postgres_local():
    """Check if PostgreSQL is running locally"""
    try:
        result = subprocess.run(['pg_isready', '-h', 'localhost', '-p', '5432'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL is running locally")
            return True
        else:
            print("❌ PostgreSQL is not running locally")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL client tools not found")
        return False

def setup_local_postgres():
    """Setup instructions for local PostgreSQL"""
    print("\n🗄️ Local PostgreSQL Setup Instructions:")
    print("1. Install PostgreSQL:")
    print("   Ubuntu/Debian: sudo apt install postgresql postgresql-contrib")
    print("   macOS: brew install postgresql")
    print("   Windows: Download from https://www.postgresql.org/download/")
    
    print("\n2. Start PostgreSQL service:")
    print("   Ubuntu/Debian: sudo systemctl start postgresql")
    print("   macOS: brew services start postgresql")
    
    print("\n3. Create database:")
    print("   sudo -u postgres createdb smart_recommender")
    print("   OR")
    print("   sudo -u postgres psql")
    print("   CREATE DATABASE smart_recommender;")
    print("   \\q")
    
    print("\n4. Run migrations:")
    print("   alembic upgrade head")

def check_environment():
    """Check the current environment setup"""
    print("🔍 Checking Environment Setup...")
    
    # Check .env file
    if Path('.env').exists():
        print("✅ .env file exists")
    else:
        print("❌ .env file missing")
        return False
    
    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is active")
    else:
        print("❌ Virtual environment is not active")
        return False
    
    # Check dependencies
    try:
        import psycopg2
        print("✅ psycopg2 is installed")
    except ImportError:
        print("❌ psycopg2 is not installed")
        return False
    
    try:
        import alembic
        print("✅ alembic is installed")
    except ImportError:
        print("❌ alembic is not installed")
        return False
    
    return True

def create_database():
    """Create the database if it doesn't exist"""
    print("\n🗄️ Creating database...")
    try:
        result = subprocess.run(['sudo', '-u', 'postgres', 'createdb', 'smart_recommender'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database 'smart_recommender' created successfully")
            return True
        elif "already exists" in result.stderr:
            print("✅ Database 'smart_recommender' already exists")
            return True
        else:
            print(f"❌ Failed to create database: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def run_migrations():
    """Run database migrations"""
    print("\n🔄 Running database migrations...")
    try:
        result = subprocess.run(['alembic', 'upgrade', 'head'], check=True)
        print("✅ Database migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 StuckAI for Travel - Local Development Setup")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment setup incomplete. Please fix the issues above.")
        return
    
    # Check PostgreSQL
    postgres_running = check_postgres_local()
    
    print("\n" + "=" * 60)
    print("📋 Setup Options:")
    
    if postgres_running:
        print("1. 🗄️ Setup database and run migrations")
        print("   - Create database if it doesn't exist")
        print("   - Run all migrations")
        print("   - Ready to start development")
    
    print("2. 📖 View setup instructions only")
    print("3. 🗄️ Create database only")
    print("4. 🔄 Run migrations only")
    
    choice = input("\nSelect an option (1-4): ").strip()
    
    if choice == "1" and postgres_running:
        if create_database() and run_migrations():
            print("\n🎉 Setup completed successfully!")
            print("You can now start the application with:")
            print("  uvicorn app.main:app --reload")
        else:
            print("\n❌ Setup failed. Please check the error messages above.")
    
    elif choice == "2":
        setup_local_postgres()
    
    elif choice == "3":
        if create_database():
            print("\n✅ Database created successfully!")
        else:
            print("\n❌ Database creation failed!")
    
    elif choice == "4":
        if run_migrations():
            print("\n✅ Migrations completed successfully!")
        else:
            print("\n❌ Migrations failed!")
    
    else:
        print("Invalid choice or PostgreSQL is not running.")

if __name__ == "__main__":
    main() 