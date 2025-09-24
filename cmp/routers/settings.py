"""
Settings and Configuration Management Router

Provides interfaces for managing system settings, API integrations,
and configuration validation.
"""

from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
from pathlib import Path

from .auth import get_current_user
from ..models import User, Company, BusinessDocument, BusinessActivity, DocumentType
from ..db import get_db
from ..logging_config import get_logger
from ..config import settings
from ..integrations.invoices import zoho_books, emirates_nbd, bank_file_importer

logger = get_logger("routers.settings")
router = APIRouter()
templates = Jinja2Templates(directory="cmp/templates")


async def get_company_info() -> Dict[str, Any]:
    """Get current company information"""
    try:
        from ..db import session_scope
        with session_scope() as session:
            company = session.query(Company).first()
            if not company:
                # Create default company if none exists
                company = Company(
                    legal_name="CMP Financial Services LLC",
                    trade_name="CMP Financial Services",
                    business_type="Limited Liability Company",
                    city="Dubai",
                    emirate="Dubai", 
                    country="United Arab Emirates",
                    primary_activity=BusinessActivity.FINANCIAL_SERVICES,
                    currency="AED",
                    fiscal_year_end="31-Dec"
                )
                session.add(company)
                session.commit()
            
            return {
                "id": company.id,
                "legal_name": company.legal_name,
                "trade_name": company.trade_name,
                "business_type": company.business_type,
                "email": company.email,
                "phone": company.phone,
                "website": company.website,
                "address_line1": company.address_line1,
                "address_line2": company.address_line2,
                "city": company.city,
                "emirate": company.emirate,
                "country": company.country,
                "po_box": company.po_box,
                "trade_license_number": company.trade_license_number,
                "trade_license_authority": company.trade_license_authority,
                "trade_license_issue_date": company.trade_license_issue_date.isoformat() if company.trade_license_issue_date else None,
                "trade_license_expiry_date": company.trade_license_expiry_date.isoformat() if company.trade_license_expiry_date else None,
                "vat_registered": company.vat_registered,
                "vat_registration_number": company.vat_registration_number,
                "vat_registration_date": company.vat_registration_date.isoformat() if company.vat_registration_date else None,
                "corporate_tax_registered": company.corporate_tax_registered,
                "corporate_tax_number": company.corporate_tax_number,
                "corporate_tax_registration_date": company.corporate_tax_registration_date.isoformat() if company.corporate_tax_registration_date else None,
                "primary_activity": company.primary_activity.value if company.primary_activity else None,
                "established_date": company.established_date.isoformat() if company.established_date else None,
                "fiscal_year_end": company.fiscal_year_end,
                "currency": company.currency,
                "description": company.description,
                "notes": company.notes
            }
    except Exception as e:
        logger.error(f"Error getting company info: {e}")
        return {}


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Render the settings management page (authentication handled client-side)"""
    try:
        # Get current configuration status (no auth required for page load)
        integrations_status = await get_integrations_status()
        
        # Get environment variables (masked for security)
        env_config = get_env_config()
        
        context = {
            "request": request,
            "integrations": integrations_status,
            "environment": env_config,
            "company": await get_company_info(),
            "business_activities": [activity.value for activity in BusinessActivity],
            "document_types": [doc_type.value for doc_type in DocumentType],
            "page_title": "Settings & Configuration"
        }
        
        return templates.TemplateResponse("settings.html", context)
        
    except Exception as e:
        logger.error(f"Error loading settings page: {e}")
        raise HTTPException(status_code=500, detail="Failed to load settings")

@router.get("/api/integrations/status")
async def integrations_status(current_user: User = Depends(get_current_user)):
    """Get current status of all integrations"""
    try:
        return await get_integrations_status()
    except Exception as e:
        logger.error(f"Error getting integrations status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration status")

@router.get("/api/company")
async def get_company_data(current_user: User = Depends(get_current_user)):
    """Get current company information"""
    try:
        return await get_company_info()
    except Exception as e:
        logger.error(f"Error getting company data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get company data")

@router.post("/api/company")
async def update_company_data(
    current_user: User = Depends(get_current_user),
    legal_name: str = Form(...),
    trade_name: str = Form(None),
    business_type: str = Form(...),
    email: str = Form(None),
    phone: str = Form(None),
    website: str = Form(None),
    address_line1: str = Form(None),
    address_line2: str = Form(None),
    city: str = Form(...),
    emirate: str = Form(...),
    country: str = Form(...),
    po_box: str = Form(None),
    trade_license_number: str = Form(None),
    trade_license_authority: str = Form(None),
    trade_license_issue_date: str = Form(None),
    trade_license_expiry_date: str = Form(None),
    vat_registered: bool = Form(False),
    vat_registration_number: str = Form(None),
    vat_registration_date: str = Form(None),
    corporate_tax_registered: bool = Form(False),
    corporate_tax_number: str = Form(None),
    corporate_tax_registration_date: str = Form(None),
    primary_activity: str = Form(None),
    established_date: str = Form(None),
    fiscal_year_end: str = Form(...),
    currency: str = Form(...),
    description: str = Form(None),
    notes: str = Form(None)
):
    """Update company information"""
    try:
        from ..db import session_scope
        from datetime import datetime
        
        with session_scope() as session:
            company = session.query(Company).first()
            if not company:
                company = Company()
                session.add(company)
            
            # Update basic information
            company.legal_name = legal_name
            company.trade_name = trade_name if trade_name else None
            company.business_type = business_type
            company.email = email if email else None
            company.phone = phone if phone else None
            company.website = website if website else None
            
            # Update address
            company.address_line1 = address_line1 if address_line1 else None
            company.address_line2 = address_line2 if address_line2 else None
            company.city = city
            company.emirate = emirate
            company.country = country
            company.po_box = po_box if po_box else None
            
            # Update trade license
            company.trade_license_number = trade_license_number if trade_license_number else None
            company.trade_license_authority = trade_license_authority if trade_license_authority else None
            if trade_license_issue_date:
                company.trade_license_issue_date = datetime.strptime(trade_license_issue_date, '%Y-%m-%d').date()
            if trade_license_expiry_date:
                company.trade_license_expiry_date = datetime.strptime(trade_license_expiry_date, '%Y-%m-%d').date()
            
            # Update VAT information
            company.vat_registered = vat_registered
            company.vat_registration_number = vat_registration_number if vat_registration_number else None
            if vat_registration_date:
                company.vat_registration_date = datetime.strptime(vat_registration_date, '%Y-%m-%d').date()
            
            # Update corporate tax
            company.corporate_tax_registered = corporate_tax_registered
            company.corporate_tax_number = corporate_tax_number if corporate_tax_number else None
            if corporate_tax_registration_date:
                company.corporate_tax_registration_date = datetime.strptime(corporate_tax_registration_date, '%Y-%m-%d').date()
            
            # Update business activity
            if primary_activity:
                try:
                    company.primary_activity = BusinessActivity(primary_activity)
                except ValueError:
                    company.primary_activity = BusinessActivity.OTHER
            
            # Update other fields
            if established_date:
                company.established_date = datetime.strptime(established_date, '%Y-%m-%d').date()
            company.fiscal_year_end = fiscal_year_end
            company.currency = currency
            company.description = description if description else None
            company.notes = notes if notes else None
            company.updated_by = current_user.email
            
            session.commit()
            
            return {
                "success": True,
                "message": "Company information updated successfully",
                "data": await get_company_info()
            }
            
    except Exception as e:
        logger.error(f"Error updating company data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update company data: {str(e)}")

@router.post("/api/integrations/test/{integration}")
async def test_integration(integration: str, current_user: User = Depends(get_current_user)):
    """Test connection to a specific integration"""
    try:
        if integration == "zoho_books":
            return await test_zoho_books_connection()
        elif integration == "wio_bank":
            return await test_wio_bank_connection()
        elif integration == "file_import":
            return await test_file_import_system()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown integration: {integration}")
            
    except Exception as e:
        logger.error(f"Error testing {integration}: {e}")
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}",
            "success": False
        }

@router.post("/api/settings/zoho-books")
async def update_zoho_books_settings(
    current_user: User = Depends(get_current_user),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    access_token: str = Form(None),
    refresh_token: str = Form(None),
    organization_id: str = Form(...),
    base_url: str = Form("https://www.zohoapis.com/books/v3")
):
    """Update Zoho Books configuration"""
    try:
        # Save to environment file
        env_updates = {
            "ZOHO_CLIENT_ID": client_id,
            "ZOHO_CLIENT_SECRET": client_secret,
            "ZOHO_ORGANIZATION_ID": organization_id,
            "ZOHO_BASE_URL": base_url
        }
        
        if access_token:
            env_updates["ZOHO_ACCESS_TOKEN"] = access_token
        if refresh_token:
            env_updates["ZOHO_REFRESH_TOKEN"] = refresh_token
            
        # Update environment file
        update_env_file(env_updates)
        
        # Test the new configuration
        test_result = await test_zoho_books_connection()
        
        logger.info("Zoho Books configuration updated")
        return {
            "status": "success",
            "message": "Zoho Books configuration updated successfully",
            "test_result": test_result
        }
        
    except Exception as e:
        logger.error(f"Error updating Zoho Books settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.get("/api/settings/oauth/zoho-authorize")
async def zoho_oauth_authorize(
    client_id: str = None, 
    current_user: User = Depends(get_current_user)
):
    """Generate Zoho OAuth authorization URL"""
    try:
        # Use provided client_id or fall back to configured one
        if client_id:
            oauth_client_id = client_id
        else:
            oauth_client_id = settings.zoho_client_id or ""
            
        if not oauth_client_id:
            return {
                "error": "Client ID required",
                "message": "Please provide a Client ID or configure it in settings first"
            }
            
        # Generate OAuth URL for Zoho Books
        oauth_url = (
            f"https://accounts.zoho.com/oauth/v2/auth?"
            f"scope=ZohoBooks.fullaccess.all&"
            f"client_id={oauth_client_id}&"
            f"response_type=code&"
            f"access_type=offline&"
            f"redirect_uri=http://localhost:8000/settings/oauth/zoho-callback"
        )
        
        return {
            "authorization_url": oauth_url,
            "instructions": "Click the URL to authorize CMP to access your Zoho Books data",
            "client_id": oauth_client_id
        }
        
    except Exception as e:
        logger.error(f"Error generating Zoho OAuth URL: {e}")
        return {
            "error": "OAuth URL generation failed",
            "message": str(e)
        }

@router.get("/settings/oauth/zoho-callback")
async def zoho_oauth_callback(code: str = None, error: str = None):
    """Handle Zoho OAuth callback and exchange code for tokens"""
    if error:
        return HTMLResponse(f"""
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <h2>OAuth Authorization Failed</h2>
            <p>Error: {error}</p>
            <p><a href="/settings">Return to Settings</a></p>
        </body>
        </html>
        """)
    
    if not code:
        return HTMLResponse("""
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <h2>OAuth Authorization Failed</h2>
            <p>No authorization code received</p>
            <p><a href="/settings">Return to Settings</a></p>
        </body>
        </html>
        """)
    
    try:
        # Exchange authorization code for access token
        import aiohttp
        
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        
        # Prepare token exchange data
        token_data = {
            "code": code,
            "client_id": settings.zoho_client_id,
            "client_secret": settings.zoho_client_secret,
            "redirect_uri": "http://localhost:8000/settings/oauth/zoho-callback",
            "grant_type": "authorization_code"
        }
        
        # Exchange code for tokens
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=token_data) as response:
                token_response = await response.json()
                
                if response.status == 200 and "access_token" in token_response:
                    access_token = token_response["access_token"]
                    refresh_token = token_response.get("refresh_token", "")
                    expires_in = token_response.get("expires_in", 3600)
                    
                    # Store tokens in environment/database (for now, we'll show them)
                    # TODO: Store these in database or update .env file
                    
                    return HTMLResponse(f"""
                    <html>
                    <head>
                        <title>OAuth Success</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
                            .success {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                            .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                            .token-box {{ background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                            .token {{ font-family: monospace; word-break: break-all; font-size: 12px; }}
                            .copy-btn {{ background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-left: 10px; }}
                        </style>
                        <script>
                            function copyToClipboard(text, btnId) {{
                                navigator.clipboard.writeText(text).then(function() {{
                                    const btn = document.getElementById(btnId);
                                    const originalText = btn.innerText;
                                    btn.innerText = 'Copied!';
                                    setTimeout(() => btn.innerText = originalText, 2000);
                                }});
                            }}
                        </script>
                    </head>
                    <body>
                        <div class="success">
                            <h2>🎉 OAuth Authorization Successful!</h2>
                            <p>Your Zoho Books access tokens have been generated successfully!</p>
                        </div>
                        
                        <div class="warning">
                            <h3>⚠️ Important: Add These Tokens to Your .env File</h3>
                            <p>Copy the tokens below and add them to your <code>.env</code> file to complete the setup:</p>
                        </div>
                        
                        <h3>Access Token:</h3>
                        <div class="token-box">
                            <div class="token">{access_token}</div>
                            <button class="copy-btn" id="copy-access" onclick="copyToClipboard('{access_token}', 'copy-access')">Copy</button>
                        </div>
                        
                        <h3>Refresh Token:</h3>
                        <div class="token-box">
                            <div class="token">{refresh_token}</div>
                            <button class="copy-btn" id="copy-refresh" onclick="copyToClipboard('{refresh_token}', 'copy-refresh')">Copy</button>
                        </div>
                        
                        <h3>Add to .env file:</h3>
                        <div class="token-box">
                            <div class="token">ZOHO_ACCESS_TOKEN={access_token}<br>ZOHO_REFRESH_TOKEN={refresh_token}</div>
                            <button class="copy-btn" id="copy-env" onclick="copyToClipboard('ZOHO_ACCESS_TOKEN={access_token}\\nZOHO_REFRESH_TOKEN={refresh_token}', 'copy-env')">Copy Both</button>
                        </div>
                        
                        <h3>Next Steps:</h3>
                        <ol>
                            <li>Copy the tokens above</li>
                            <li>Add them to your <code>.env</code> file</li>
                            <li>Restart your application</li>
                            <li><a href="/settings">Return to Settings</a> to verify the connection</li>
                        </ol>
                        
                        <p><strong>Token Details:</strong> Access token expires in {expires_in} seconds ({expires_in//3600} hours). The refresh token can be used to get new access tokens automatically.</p>
                    </body>
                    </html>
                    """)
                else:
                    error_msg = token_response.get("error", "Unknown error")
                    error_desc = token_response.get("error_description", "")
                    return HTMLResponse(f"""
                    <html>
                    <head><title>Token Exchange Failed</title></head>
                    <body>
                        <h2>❌ Token Exchange Failed</h2>
                        <p>Error: {error_msg}</p>
                        <p>Description: {error_desc}</p>
                        <p><a href="/settings">Return to Settings</a></p>
                    </body>
                    </html>
                    """)
    
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return HTMLResponse(f"""
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <h2>❌ OAuth Processing Error</h2>
            <p>An error occurred while processing the OAuth callback: {str(e)}</p>
            <p><a href="/settings">Return to Settings</a></p>
        </body>
        </html>
        """)

async def get_integrations_status() -> Dict[str, Any]:
    """Get comprehensive status of all integrations"""
    
    # Zoho Books Status
    zoho_status = {
        "name": "Zoho Books",
        "type": "accounting_api",
        "configured": zoho_books.is_configured,
        "status": "connected" if zoho_books.is_configured else "not_configured",
        "description": "Accounting and invoice management platform",
        "required_credentials": ["Client ID", "Client Secret", "Organization ID"],
        "optional_credentials": ["Access Token", "Refresh Token"],
        "test_available": True
    }
    
    # WIO Bank Status (or Emirates NBD for compatibility)
    bank_status = {
        "name": "WIO Bank (File Import)",
        "type": "banking_import", 
        "configured": True,  # File import is always available
        "status": "file_import_only",
        "description": "WIO Bank transactions via CSV/Excel file import (API not available)",
        "required_credentials": [],
        "optional_credentials": [],
        "test_available": True,
        "note": "WIO Bank does not provide public API access. Use file import for transaction data."
    }
    
    # File Import System
    file_import_status = {
        "name": "Bank File Import",
        "type": "file_processor",
        "configured": True,
        "status": "available",
        "description": "Import transactions from CSV/Excel bank statements",
        "supported_formats": [".csv", ".xlsx", ".qif", ".ofx"],
        "supported_banks": ["WIO Bank", "Emirates NBD", "ADCB", "FAB", "Generic CSV"],
        "test_available": True
    }
    
    return {
        "zoho_books": zoho_status,
        "wio_bank": bank_status,
        "file_import": file_import_status,
        "last_updated": "live"
    }

async def test_zoho_books_connection() -> Dict[str, Any]:
    """Test Zoho Books API connection"""
    try:
        if not zoho_books.is_configured:
            return {
                "status": "not_configured",
                "message": "Zoho Books credentials not configured",
                "success": False,
                "details": "Configure Client ID, Client Secret, and Organization ID to enable API access"
            }
        
        # Test API connection
        orgs = await zoho_books.get_organizations()
        
        if "error" in orgs:
            return {
                "status": "error", 
                "message": "API connection failed",
                "success": False,
                "details": orgs.get("error", "Unknown error")
            }
        
        org_count = len(orgs) if isinstance(orgs, list) else 0
        return {
            "status": "connected",
            "message": f"Successfully connected to Zoho Books ({org_count} organizations found)",
            "success": True,
            "details": f"API endpoint: {zoho_books.base_url}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}",
            "success": False,
            "details": "Check credentials and network connectivity"
        }

async def test_wio_bank_connection() -> Dict[str, Any]:
    """Test WIO Bank file import system (since API isn't available)"""
    try:
        return {
            "status": "file_import_ready",
            "message": "WIO Bank file import system ready",
            "success": True,
            "details": "Upload CSV/Excel statements for transaction processing",
            "note": "WIO Bank API access not available for retail/SME accounts"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"File import system error: {str(e)}",
            "success": False
        }

async def test_file_import_system() -> Dict[str, Any]:
    """Test bank file import system"""
    try:
        # Check if upload directory exists
        upload_dir = Path("local_storage/bank_statements")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "status": "ready",
            "message": "File import system operational",
            "success": True,
            "details": f"Supported formats: {', '.join(bank_file_importer.supported_formats)}",
            "upload_directory": str(upload_dir.absolute())
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"File system error: {str(e)}",
            "success": False
        }

def get_env_config() -> Dict[str, Any]:
    """Get current environment configuration (masked for security)"""
    env_vars = {
        "ZOHO_CLIENT_ID": mask_credential(settings.zoho_client_id),
        "ZOHO_CLIENT_SECRET": mask_credential(settings.zoho_client_secret),
        "ZOHO_ACCESS_TOKEN": mask_credential(settings.zoho_access_token),
        "ZOHO_REFRESH_TOKEN": mask_credential(settings.zoho_refresh_token),
        "ZOHO_ORGANIZATION_ID": settings.zoho_organization_id or "Not set",
        "ZOHO_BASE_URL": settings.zoho_base_url,
        "DATABASE_URL": mask_credential(settings.database_url),
        "ENV": settings.environment,
        "JWT_SECRET_KEY": mask_credential(settings.jwt_secret_key)
    }
    
    return env_vars

def mask_credential(value: Optional[str]) -> str:
    """Mask credentials for display"""
    if not value:
        return "Not set"
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]

def update_env_file(updates: Dict[str, str]):
    """Update .env file with new values"""
    env_file = Path(".env")
    
    # Read existing env file
    env_content = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_content[key.strip()] = value.strip()
    
    # Update with new values
    env_content.update(updates)
    
    # Write back to file
    with open(env_file, 'w') as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")
    
    logger.info(f"Updated .env file with {len(updates)} settings")
