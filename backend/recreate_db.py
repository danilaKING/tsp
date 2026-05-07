#!/usr/bin/env python3
"""
Script to drop and recreate all database tables.
This is needed when schema changes occur (e.g., adding new columns).
"""

from database import engine, Base
from models import User, Question, Interview, Message, Feedback, ProductMetric

def recreate_database():
    """Drop all tables and recreate them"""
    print("⚠️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ Tables dropped")
    
    print("📝 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
    
    print("\n✅ Database schema updated!")
    print("📌 Run 'python seed_questions.py' to populate test questions")

if __name__ == "__main__":
    import sys
    
    # Confirm before dropping
    if "--force" not in sys.argv:
        response = input("⚠️  This will DELETE all data. Continue? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(1)
    
    recreate_database()
