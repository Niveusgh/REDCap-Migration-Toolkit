#!/usr/bin/env python3
"""
REDCap Data Migration Toolkit
Main script for executing migrations from legacy systems to REDCap
Author: Thea Francis
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

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
        logging.FileHandler(f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Migrate data from legacy systems to REDCap')
    parser.add_argument('--config', required=True, help='Path to configuration file')
    parser.add_argument('--source', required=True, help='Path to source data file')
    parser.add_argument('--mapping', required=True, help='Path to mapping template file')
    parser.add_argument('--redcap-url', required=True, help='REDCap API URL')
    parser.add_argument('--api-key', required=True, help='REDCap API key')
    parser.add_argument('--validate-only', action='store_true', help='Only validate data without migration')
    parser.add_argument('--secure-mode', action='store_true', help='Enable enhanced PHI security handling')
    
    return parser.parse_args()

def load_config(config_path):
    """Load configuration from file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

def main():
    """Main migration function."""
    args = parse_arguments()
    config = load_config(args.config)
    
    logger.info("Starting REDCap data migration process")
    logger.info(f"Source: {args.source}")
    logger.info(f"Target: {args.redcap_url}")
    
    try:
        # Initialize components
        security = SecurityHandler(secure_mode=args.secure_mode)
        mapper = DataMapper(args.mapping)
        validator = DataValidator(config.get('validation_rules', {}))
        migrator = DataMigrator(args.redcap_url, args.api_key)
        reporter = MigrationReporter()
        
        # Load and secure source data
        logger.info("Loading source data...")
        source_data = security.load_and_secure_data(args.source)
        
        # Map data
        logger.info("Mapping data to REDCap format...")
        mapped_data = mapper.map_data(source_data)
        
        # Validate data
        logger.info("Validating data...")
        validation_results = validator.validate(mapped_data)
        reporter.report_validation_results(validation_results)
        
        if not validation_results['is_valid']:
            logger.error("Data validation failed")
            sys.exit(1)
        
        if args.validate_only:
            logger.info("Validation complete (validate-only mode)")
            sys.exit(0)
        
        # Perform migration
        logger.info("Performing migration...")
        migration_result = migrator.migrate(mapped_data)
        
        # Report results
        reporter.report_migration_results(migration_result)
        logger.info(f"Migration completed: {migration_result['records_processed']} records processed")
        logger.info(f"Success rate: {migration_result['success_rate']:.2f}%")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()