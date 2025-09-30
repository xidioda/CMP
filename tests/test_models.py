"""
Comprehensive unit tests for models module (models.py)
Tests SQLAlchemy models, relationships, and data validation.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cmp.models import (
    Base, User, UserRole, CompanySettings, Customer, Project, 
    Invoice, Item, Transaction, BankStatement
)


class TestUserModel:
    """Test suite for User model"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_user_creation(self, db_session):
        """Test creating a new user"""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            role=UserRole.USER,
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.created_at is not None
    
    def test_user_roles(self):
        """Test user role enumeration"""
        assert UserRole.ADMIN == "admin"
        assert UserRole.MANAGER == "manager"
        assert UserRole.USER == "user"
    
    def test_user_email_uniqueness(self, db_session):
        """Test that user emails must be unique"""
        user1 = User(
            email="duplicate@example.com",
            hashed_password="password1",
            full_name="User One",
            role=UserRole.USER
        )
        
        user2 = User(
            email="duplicate@example.com",
            hashed_password="password2",
            full_name="User Two",
            role=UserRole.USER
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
    
    def test_user_string_representation(self):
        """Test user string representation"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER
        )
        
        assert str(user) == "Test User <test@example.com>"


class TestCompanySettingsModel:
    """Test suite for CompanySettings model"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_company_settings_creation(self, db_session):
        """Test creating company settings"""
        settings = CompanySettings(
            company_name="Test Company",
            address="123 Test St",
            phone="+1234567890",
            email="company@test.com",
            website="https://test.com",
            tax_id="TAX123456"
        )
        
        db_session.add(settings)
        db_session.commit()
        
        assert settings.id is not None
        assert settings.company_name == "Test Company"
        assert settings.address == "123 Test St"
        assert settings.phone == "+1234567890"
        assert settings.email == "company@test.com"
        assert settings.website == "https://test.com"
        assert settings.tax_id == "TAX123456"
        assert settings.created_at is not None
        assert settings.updated_at is not None


class TestCustomerModel:
    """Test suite for Customer model"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_customer_creation(self, db_session):
        """Test creating a new customer"""
        customer = Customer(
            name="Test Customer",
            email="customer@test.com",
            phone="+1234567890",
            address="456 Customer Ave",
            zoho_contact_id="ZOHO123"
        )
        
        db_session.add(customer)
        db_session.commit()
        
        assert customer.id is not None
        assert customer.name == "Test Customer"
        assert customer.email == "customer@test.com"
        assert customer.phone == "+1234567890"
        assert customer.address == "456 Customer Ave"
        assert customer.zoho_contact_id == "ZOHO123"
        assert customer.created_at is not None
    
    def test_customer_projects_relationship(self, db_session):
        """Test customer-projects relationship"""
        customer = Customer(name="Test Customer", email="test@customer.com")
        db_session.add(customer)
        db_session.commit()
        
        project = Project(
            name="Test Project",
            customer_id=customer.id,
            start_date=date.today(),
            status="active"
        )
        db_session.add(project)
        db_session.commit()
        
        # Refresh customer to load relationships
        db_session.refresh(customer)
        
        assert len(customer.projects) == 1
        assert customer.projects[0].name == "Test Project"


class TestProjectModel:
    """Test suite for Project model"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_project_creation(self, db_session):
        """Test creating a new project"""
        # Create customer first
        customer = Customer(name="Test Customer", email="test@customer.com")
        db_session.add(customer)
        db_session.commit()
        
        project = Project(
            name="Test Project",
            description="A test project",
            customer_id=customer.id,
            start_date=date.today(),
            budget=Decimal("10000.00"),
            status="active",
            zoho_project_id="ZOHO_PROJ_123"
        )
        
        db_session.add(project)
        db_session.commit()
        
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.customer_id == customer.id
        assert project.start_date == date.today()
        assert project.budget == Decimal("10000.00")
        assert project.status == "active"
        assert project.zoho_project_id == "ZOHO_PROJ_123"
        assert project.created_at is not None
    
    def test_project_customer_relationship(self, db_session):
        """Test project-customer relationship"""
        customer = Customer(name="Test Customer", email="test@customer.com")
        db_session.add(customer)
        db_session.commit()
        
        project = Project(
            name="Test Project",
            customer_id=customer.id,
            start_date=date.today(),
            status="active"
        )
        db_session.add(project)
        db_session.commit()
        
        # Test relationship
        assert project.customer.name == "Test Customer"
        assert project.customer.email == "test@customer.com"


class TestInvoiceModel:
    """Test suite for Invoice model"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_invoice_creation(self, db_session):
        """Test creating a new invoice"""
        # Create customer first
        customer = Customer(name="Test Customer", email="test@customer.com")
        db_session.add(customer)
        db_session.commit()
        
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-001",
            amount=Decimal("1500.00"),
            tax_amount=Decimal("150.00"),
            total_amount=Decimal("1650.00"),
            status="sent",
            issue_date=date.today(),
            due_date=date.today(),
            zoho_invoice_id="ZOHO_INV_123"
        )
        
        db_session.add(invoice)
        db_session.commit()
        
        assert invoice.id is not None
        assert invoice.customer_id == customer.id
        assert invoice.invoice_number == "INV-001"
        assert invoice.amount == Decimal("1500.00")
        assert invoice.tax_amount == Decimal("150.00")
        assert invoice.total_amount == Decimal("1650.00")
        assert invoice.status == "sent"
        assert invoice.zoho_invoice_id == "ZOHO_INV_123"
        assert invoice.created_at is not None


class TestItemModel:
    """Test suite for Item model"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_item_creation(self, db_session):
        """Test creating a new item"""
        item = Item(
            name="Test Service",
            description="A test service item",
            rate=Decimal("100.00"),
            unit="hour",
            item_type="service",
            sku="TEST-001",
            zoho_item_id="ZOHO_ITEM_123"
        )
        
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.name == "Test Service"
        assert item.description == "A test service item"
        assert item.rate == Decimal("100.00")
        assert item.unit == "hour"
        assert item.item_type == "service"
        assert item.sku == "TEST-001"
        assert item.zoho_item_id == "ZOHO_ITEM_123"
        assert item.created_at is not None


class TestTransactionModel:
    """Test suite for Transaction model"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_transaction_creation(self, db_session):
        """Test creating a new transaction"""
        transaction = Transaction(
            amount=Decimal("500.00"),
            description="Test transaction",
            transaction_date=date.today(),
            category="business_expense",
            account="checking",
            reference_number="REF123",
            zoho_transaction_id="ZOHO_TXN_123"
        )
        
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.id is not None
        assert transaction.amount == Decimal("500.00")
        assert transaction.description == "Test transaction"
        assert transaction.transaction_date == date.today()
        assert transaction.category == "business_expense"
        assert transaction.account == "checking"
        assert transaction.reference_number == "REF123"
        assert transaction.zoho_transaction_id == "ZOHO_TXN_123"
        assert transaction.created_at is not None


class TestBankStatementModel:
    """Test suite for BankStatement model"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_bank_statement_creation(self, db_session):
        """Test creating a new bank statement"""
        statement = BankStatement(
            account_name="Business Checking",
            statement_date=date.today(),
            beginning_balance=Decimal("5000.00"),
            ending_balance=Decimal("5500.00"),
            processed=False,
            file_path="/path/to/statement.pdf"
        )
        
        db_session.add(statement)
        db_session.commit()
        
        assert statement.id is not None
        assert statement.account_name == "Business Checking"
        assert statement.statement_date == date.today()
        assert statement.beginning_balance == Decimal("5000.00")
        assert statement.ending_balance == Decimal("5500.00")
        assert statement.processed is False
        assert statement.file_path == "/path/to/statement.pdf"
        assert statement.created_at is not None


@pytest.mark.integration
class TestModelRelationships:
    """Integration tests for model relationships"""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        yield session
        session.close()
    
    def test_complete_business_workflow(self, db_session):
        """Test complete business workflow with all models"""
        # Create customer
        customer = Customer(name="ABC Corp", email="contact@abc.com")
        db_session.add(customer)
        db_session.commit()
        
        # Create project
        project = Project(
            name="Website Development",
            customer_id=customer.id,
            start_date=date.today(),
            budget=Decimal("15000.00"),
            status="active"
        )
        db_session.add(project)
        db_session.commit()
        
        # Create items
        item = Item(
            name="Web Development",
            rate=Decimal("150.00"),
            unit="hour",
            item_type="service"
        )
        db_session.add(item)
        db_session.commit()
        
        # Create invoice
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-2025-001",
            amount=Decimal("7500.00"),
            tax_amount=Decimal("750.00"),
            total_amount=Decimal("8250.00"),
            status="sent",
            issue_date=date.today(),
            due_date=date.today()
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Verify relationships
        db_session.refresh(customer)
        assert len(customer.projects) == 1
        assert len(customer.invoices) == 1
        assert customer.projects[0].name == "Website Development"
        assert customer.invoices[0].invoice_number == "INV-2025-001"