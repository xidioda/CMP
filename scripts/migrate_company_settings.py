#!/usr/bin/env python3
"""
Database Migration Script: Add Company Settings Tables

This script adds the new Company and BusinessDocument tables to the existing database.
"""

import asyncio
from sqlalchemy import text
from cmp.db import engine, Base, session_scope
from cmp.models import Company, BusinessDocument, BusinessActivity, DocumentType
from cmp.logging_config import get_logger
import datetime as dt

logger = get_logger("migration.company_settings")


async def create_tables():
    """Create the new company and document tables"""
    try:
        logger.info("Creating company settings tables...")
        
        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Company settings tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False


async def create_default_company():
    """Create a default company record"""
    try:
        with session_scope() as session:
            # Check if company already exists
            existing = session.execute(text("SELECT COUNT(*) FROM companies")).scalar()
            
            if existing > 0:
                logger.info("Company record already exists, skipping default creation")
                return True
            
            # Create default company record
            default_company = Company(
                legal_name="CMP Financial Services LLC",
                trade_name="CMP Financial Services",
                business_type="Limited Liability Company",
                city="Dubai",
                emirate="Dubai",
                country="United Arab Emirates",
                primary_activity=BusinessActivity.FINANCIAL_SERVICES,
                currency="AED",
                fiscal_year_end="31-Dec",
                description="Comprehensive Management Platform - AI-powered financial management services",
                established_date=dt.date(2024, 1, 1),
                updated_by="system_migration"
            )
            
            session.add(default_company)
            session.commit()
            
            logger.info("✅ Default company record created")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creating default company: {e}")
        return False


async def verify_migration():
    """Verify that the migration was successful"""
    try:
        with session_scope() as session:
            # Check companies table
            company_count = session.execute(text("SELECT COUNT(*) FROM companies")).scalar()
            logger.info(f"Companies table: {company_count} records")
            
            # Check business_documents table  
            docs_count = session.execute(text("SELECT COUNT(*) FROM business_documents")).scalar()
            logger.info(f"Business documents table: {docs_count} records")
            
            # Check if default company was created
            if company_count > 0:
                company = session.execute(text("SELECT legal_name, vat_registered FROM companies LIMIT 1")).fetchone()
                logger.info(f"Default company: {company[0]}, VAT registered: {company[1]}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")
        return False


async def main():
    """Run the complete migration"""
    logger.info("🚀 Starting company settings migration...")
    
    # Step 1: Create tables
    if not await create_tables():
        logger.error("Migration failed at table creation")
        return False
    
    # Step 2: Create default company
    if not await create_default_company():
        logger.error("Migration failed at default company creation")
        return False
    
    # Step 3: Verify migration
    if not await verify_migration():
        logger.error("Migration verification failed")
        return False
    
    logger.info("🎉 Company settings migration completed successfully!")
    return True


if __name__ == "__main__":
    asyncio.run(main())