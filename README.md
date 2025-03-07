# REDCap Data Migration Toolkit

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Status: Beta](https://img.shields.io/badge/Status-Beta-orange.svg)

A comprehensive toolkit for securely migrating data from legacy systems to REDCap while maintaining data integrity and regulatory compliance.

## 🔍 Overview

REDCap (Research Electronic Data Capture) is a secure, web-based application designed to support data capture for research studies. It provides an intuitive interface for validated data entry, audit trails, automated export procedures, and seamless data integration with external sources. REDCap is widely used in healthcare and research institutions worldwide to collect and manage sensitive research data in a HIPAA-compliant environment.

This toolkit provides a set of utilities and best practices for handling one of the most challenging aspects of REDCap administration: migrating existing research data from legacy systems into REDCap's data structure. Developed based on real-world migration projects across multiple university research environments, these tools are designed to streamline the migration process while ensuring data integrity and regulatory compliance.

## ✨ Features

### 🔄 Data Mapping Framework
- Flexible templates for mapping source data to REDCap data dictionary structures
- Support for complex data types including calculated fields, checkboxes, and file uploads
- Handling for special characters and encoding issues common in research datasets

### ✅ Validation Engine
- Pre-migration validation to identify potential data format issues
- Data type compliance checking against REDCap field restrictions
- Identification of missing required fields before migration begins
- Branching logic validation to ensure conditional dependencies are preserved

### 🚀 Migration Utilities
- Clean conversion of datetime formats across different systems
- Longitudinal data structure support with proper event mapping
- Repeating instruments data handling
- File attachment migration with proper metadata preservation

### 🔒 Security & Compliance
- PHI identification and handling in accordance with HIPAA regulations
- Data anonymization options for sensitive datasets
- Comprehensive logging for audit trail requirements
- Encryption handling for secure data transfer

### 📊 Reporting
- Migration summary reports with success/error metrics
- Detailed error logs with actionable remediation steps
- Visual data validation dashboards to verify migration accuracy

## 📁 Project Structure

```
redcap-migration-toolkit/
│
├── migrate.py                       # Main script for running migrations
├── README.md                        # This file
├── LICENSE                          # MIT License file
├── requirements.txt                 # Python dependencies
│
├── redcap_migration/                # Core code
│   ├── __init__.py
│   ├── mapper.py                    # Maps source data to REDCap format
│   ├── validator.py                 # Validates data before and after migration
│   ├── migrator.py                  # Handles the migration process
│   ├── security.py                  # PHI handling and data security
│   └── reporter.py                  # Generates migration reports
│
├── templates/                       # Example mapping templates
│   ├── csv_to_redcap.json           # CSV mapping example
│   └── excel_to_redcap.json         # Excel mapping example
│
├── examples/                        # Example usage scripts
│   ├── basic_migration.py           # Simple migration example
│   └── longitudinal_migration.py    # Complex data structure example
│
└── docs/                            # Documentation
    ├── getting_started.md           # Quick start guide
    ├── best_practices.md            # Migration best practices
    └── example_workflow.svg         # Visual workflow diagram
```

## 🚀 Getting Started

To quickly get up and running with the REDCap Data Migration Toolkit, see our [Getting Started Guide](docs/getting_started.md).

## 📚 Documentation

- [Getting Started Guide](docs/getting_started.md)
- [Best Practices for REDCap Migrations](docs/best_practices.md)
- [Workflow Diagram](docs/example_workflow.svg)

## 📋 Prerequisites

- Python 3.8 or higher
- Access to source data system
- REDCap API credentials (with appropriate permissions)
- REDCap data dictionary for destination project

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/redcap-migration-toolkit.git
cd redcap-migration-toolkit

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🧪 Example Usage

### Basic Migration

For a simple migration from CSV to REDCap:

```bash
python examples/basic_migration.py
```

### Longitudinal Data Migration

For complex longitudinal data with multiple events:

```bash
python examples/longitudinal_migration.py
```

## 🌟 Use Cases

This toolkit was developed and refined during data migration projects for research databases at multiple universities, including:

- Migration of 2,000+ participant records from legacy systems
- Conversion of longitudinal assessment data with complex branching logic
- Integration of healthcare referral systems with secure e-consent mechanisms
- Preservation of multi-year research data with 99.7% integrity verification

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Developed based on experiences with REDCap implementations at multiple research institutions
- Inspired by the needs of healthcare researchers working with sensitive participant data
- Special thanks to the REDCap community for their ongoing support and documentation