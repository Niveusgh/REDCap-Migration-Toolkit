#!/usr/bin/env python3
"""
Basic Migration Example
A simple demonstration of migrating data from a CSV file to REDCap
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from redcap_migration.mapper import DataMapper
from redcap_migration.validator import DataValidator
from redcap_migration.migrator import DataMigrator
from redcap_migration.security import SecurityHandler
from redcap_migration.reporter import MigrationReporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"basic_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_basic_migration():
    """Run a basic migration from CSV to REDCap"""
    
    # Configuration - replace with your actual values
    source_file = "data/sample_patients.csv"
    mapping_file = "../templates/csv_to_redcap.json"
    redcap_url = "https://redcap.example.edu/api/"
    api_key = "YOUR_API_KEY"  # Replace with your actual API key
    
    logger.info("Starting basic migration example")
    logger.info(f"Source: {source_file}")
    logger.info(f"Target: {redcap_url}")
    
    # Create output directory for reports
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize components
        security = SecurityHandler(secure_mode=False)  # Non-secure mode for example
        mapper = DataMapper(mapping_file)
        
        # Load validation rules from mapping file
        with open(mapping_file, 'r') as f:
            mapping_config = json.load(f)
        validation_rules = mapping_config.get("validation_rules", {})
        
        validator = DataValidator(validation_rules)
        migrator = DataMigrator(redcap_url, api_key, batch_size=50)
        reporter = MigrationReporter(output_dir=output_dir)
        
        # Step 1: Load source data
        logger.info("Loading source data...")
        source_data = security.load_and_secure_data(source_file)
        logger.info(f"Loaded {len(source_data)} records from source")
        
        # Step 2: Map data to REDCap format
        logger.info("Mapping data to REDCap format...")
        mapped_data = mapper.map_data(source_data)
        
        # Step 3: Validate data
        logger.info("Validating data...")
        validation_results = validator.validate(mapped_data)
        reporter.report_validation_results(validation_results)
        
        if not validation_results['is_valid']:
            logger.error("Validation failed. Please check the validation report.")
            return
        
        # Step 4: Test connection to REDCap
        logger.info("Testing connection to REDCap...")
        connection_test = migrator.test_connection()
        if not connection_test['success']:
            logger.error(f"Failed to connect to REDCap: {connection_test.get('message', 'Unknown error')}")
            return
        
        # Step 5: Perform migration
        logger.info("Performing migration...")
        migration_result = migrator.migrate(mapped_data)
        
        # Step 6: Report results
        reporter.report_migration_results(migration_result)
        
        # Summary
        success_rate = migration_result['success_rate']
        logger.info(f"Migration completed with {success_rate:.2f}% success rate")
        logger.info(f"Reports saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_basic_migration()