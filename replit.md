# Premium Book Inventory & Billing System

## Overview

This is a comprehensive book inventory and billing management system built with Streamlit. The application provides a complete solution for managing multiple book stores or publishing companies, including inventory tracking, customer management, sales, purchasing, and professional PDF invoice generation.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit (Python web framework)
- **UI Design**: Custom CSS with gradient themes and modern styling
- **Navigation**: Multi-page application with sidebar navigation
- **Interactive Elements**: Forms, data tables, charts, and real-time updates

### Backend Architecture
- **Database**: SQLite3 with custom database manager
- **Models**: Dataclass-based models for Companies, Books, Customers, and Transactions
- **Business Logic**: Separation of concerns with dedicated modules for different functionalities

### Data Storage Solutions
- **Primary Database**: SQLite3 (inventory_system.db)
- **Session Management**: Streamlit session state for cart functionality and user preferences
- **File Storage**: PDF generation for invoices and reports

## Key Components

### 1. Database Management (`database/db_manager.py`)
- SQLite3 database with proper connection handling
- CRUD operations for all entities
- Query execution with error handling
- Database schema management

### 2. Data Models (`models/`)
- **Company**: Business entity management with validation
- **Book**: Book inventory with multi-language support (Hindi/English)
- **Customer**: Customer relationship management
- **Transaction**: Purchase and sales transaction handling

### 3. User Interface Pages (`pages/`)
- **Dashboard**: Business analytics and KPIs
- **Companies**: Multi-company management
- **Books**: Inventory management with stock tracking
- **Customers**: Customer database management
- **Purchase**: Procurement and stock management
- **Sales**: Sales transactions and cart functionality
- **Billing**: Professional PDF invoice generation
- **Reports**: Comprehensive business reports and analytics

### 4. Utility Functions (`utils/`)
- **Helpers**: Common utilities for validation, formatting, and session management
- **PDF Generator**: Professional invoice and report generation using ReportLab

## Data Flow

1. **Company Setup**: Users first create company profiles
2. **Inventory Management**: Books are added to company inventories
3. **Customer Management**: Customer database is maintained per company
4. **Purchase Flow**: Stock is increased through purchase transactions
5. **Sales Flow**: Items are added to cart, then processed as sales
6. **Billing**: Professional PDF invoices are generated automatically
7. **Reporting**: Real-time analytics and business insights

## External Dependencies

### Core Dependencies
- **streamlit**: Web application framework
- **reportlab**: PDF generation for invoices
- **plotly**: Interactive charts and visualizations
- **fpdf2**: Alternative PDF generation

### System Dependencies
- **Python 3.11+**: Runtime environment
- **SQLite3**: Database (built into Python)
- **Freetype**: Font rendering support

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with Nix packages
- **Port**: 5000 (configured for Streamlit)
- **Deployment**: Autoscale deployment target
- **Workflow**: Automated Streamlit server startup

### Production Considerations
- Database file persistence across deployments
- Asset management for PDF generation
- Session state management for multi-user scenarios

### Configuration Files
- `.replit`: Replit-specific configuration
- `.streamlit/config.toml`: Streamlit theming and server settings
- `pyproject.toml`: Python project dependencies

## Key Features

### Multi-Company Support
- Manage multiple business entities
- Separate inventory and customer databases per company
- Company-specific branding for invoices

### Comprehensive Inventory Management
- Hindi and English language support for book names
- Stock tracking with damage and loss management
- Purchase price vs selling price tracking

### Professional Billing
- Auto-generated PDF invoices with company branding
- Customer details integration
- Tax calculations and terms inclusion

### Business Intelligence
- Real-time dashboard with KPIs
- Sales analytics and trends
- Stock valuation and reporting
- Low stock alerts

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- June 16, 2025. Initial setup