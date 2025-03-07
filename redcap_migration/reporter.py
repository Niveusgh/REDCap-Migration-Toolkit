"""
Migration Reporter Module
Generates reports and visualizations of migration results
"""

import logging
import json
import os
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class MigrationReporter:
    """
    Generates reports and statistics for data migration processes
    """
    
    def __init__(self, output_dir=None):
        """Initialize reporter with output directory"""
        self.output_dir = output_dir or os.getcwd()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        logger.info(f"Initialized reporter with output directory: {self.output_dir}")
    
    def report_validation_results(self, validation_results):
        """Generate report for data validation results"""
        if not validation_results:
            logger.warning("No validation results to report")
            return
        
        logger.info("Generating validation results report")
        
        # Log summary statistics
        is_valid = validation_results.get("is_valid", False)
        total_records = validation_results.get("stats", {}).get("total_records", 0)
        error_count = validation_results.get("stats", {}).get("total_errors", 0)
        warning_count = validation_results.get("stats", {}).get("total_warnings", 0)
        
        logger.info(f"Validation {'passed' if is_valid else 'failed'}")
        logger.info(f"Total records: {total_records}")
        logger.info(f"Total errors: {error_count}")
        logger.info(f"Total warnings: {warning_count}")
        
        # Log global errors and warnings
        for error in validation_results.get("errors", []):
            logger.error(f"Global error: {error}")
            
        for warning in validation_results.get("warnings", []):
            logger.warning(f"Global warning: {warning}")
        
        # Log record-specific issues
        record_issues = validation_results.get("record_issues", {})
        if record_issues:
            logger.info(f"Issues found in {len(record_issues)} records")
            
            # Log a sample of record issues (first 5)
            sample_records = list(record_issues.keys())[:5]
            for record_id in sample_records:
                issues = record_issues[record_id]
                
                for error in issues.get("errors", []):
                    logger.error(f"Record {record_id}: {error}")
                    
                for warning in issues.get("warnings", []):
                    logger.warning(f"Record {record_id}: {warning}")
        
        # Write full report to file
        report_file = os.path.join(self.output_dir, f"validation_report_{self.timestamp}.json")
        with open(report_file