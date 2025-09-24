"""
Database Migration for Zoho Books Local Storage Tables

This migration adds tables for caching Zoho Books data locally to reduce API calls:
- zoho_customers: Store customer data
- zoho_projects: Store project data  
- zoho_items: Store items/services data
- zoho_sync_status: Track synchronization status and schedules
"""

import sqlite3
import os
from pathlib import Path

def run_migration():
    """Run the migration to create Zoho Books local storage tables"""
    
    # Get the database path
    db_path = Path(__file__).parent / "cmp.db"
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Creating Zoho Books local storage tables...")
        
        # Create zoho_customers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS zoho_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zoho_customer_id VARCHAR(50) NOT NULL UNIQUE,
            customer_name VARCHAR(255) NOT NULL,
            company_name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            website VARCHAR(255),
            billing_address TEXT,
            shipping_address TEXT,
            currency_code VARCHAR(10),
            opening_balance REAL,
            credit_limit REAL,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            created_time DATETIME,
            last_modified_time DATETIME,
            last_synced DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            sync_status VARCHAR(20) NOT NULL DEFAULT 'synced'
        )
        """)
        
        # Create index on zoho_customer_id
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_zoho_customers_zoho_id ON zoho_customers(zoho_customer_id)")
        
        # Create zoho_projects table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS zoho_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zoho_project_id VARCHAR(50) NOT NULL UNIQUE,
            project_name VARCHAR(255) NOT NULL,
            project_code VARCHAR(50),
            description TEXT,
            customer_id VARCHAR(50),
            customer_name VARCHAR(255),
            budget_type VARCHAR(50),
            budget_amount REAL,
            budget_hours REAL,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            start_date DATE,
            end_date DATE,
            billing_type VARCHAR(50),
            rate REAL,
            currency_code VARCHAR(10),
            created_time DATETIME,
            last_modified_time DATETIME,
            last_synced DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            sync_status VARCHAR(20) NOT NULL DEFAULT 'synced'
        )
        """)
        
        # Create index on zoho_project_id
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_zoho_projects_zoho_id ON zoho_projects(zoho_project_id)")
        
        # Create zoho_items table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS zoho_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zoho_item_id VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            sku VARCHAR(100),
            description TEXT,
            item_type VARCHAR(50) NOT NULL DEFAULT 'sales',
            product_type VARCHAR(50),
            category_name VARCHAR(100),
            rate REAL,
            unit VARCHAR(50),
            currency_code VARCHAR(10),
            is_taxable BOOLEAN NOT NULL DEFAULT 1,
            tax_name VARCHAR(100),
            tax_percentage REAL,
            is_returnable BOOLEAN NOT NULL DEFAULT 0,
            available_stock REAL,
            stock_on_hand REAL,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            created_time DATETIME,
            last_modified_time DATETIME,
            last_synced DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            sync_status VARCHAR(20) NOT NULL DEFAULT 'synced'
        )
        """)
        
        # Create index on zoho_item_id
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_zoho_items_zoho_id ON zoho_items(zoho_item_id)")
        
        # Create zoho_sync_status table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS zoho_sync_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type VARCHAR(50) NOT NULL UNIQUE,
            last_sync_time DATETIME,
            last_successful_sync DATETIME,
            next_sync_time DATETIME,
            sync_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            records_synced INTEGER NOT NULL DEFAULT 0,
            sync_errors TEXT,
            sync_interval_minutes INTEGER NOT NULL DEFAULT 60,
            is_enabled BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create index on data_type
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_zoho_sync_status_data_type ON zoho_sync_status(data_type)")
        
        # Insert initial sync status records
        cursor.execute("""
        INSERT OR IGNORE INTO zoho_sync_status (data_type, sync_interval_minutes, is_enabled)
        VALUES 
            ('customers', 120, 1),   -- Sync customers every 2 hours
            ('projects', 60, 1),     -- Sync projects every hour  
            ('items', 240, 1)        -- Sync items every 4 hours
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("Created tables: zoho_customers, zoho_projects, zoho_items, zoho_sync_status")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()