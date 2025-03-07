#!/usr/bin/env python3
"""
Longitudinal Migration Example
Demonstrates migrating longitudinal data with multiple events to REDCap
"""

import os
import sys
import logging
import json
import pandas as pd
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
        logging.FileHandler(f"longitudinal_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LongitudinalDataHandler:
    """Helper class to handle longitudinal data structures"""
    
    def __init__(self, event_mappings):
        """Initialize with event mappings configuration"""
        self.event_mappings = event_mappings
        logger.info(f"Initialized longitudinal handler with {len(event_mappings)} events")
    
    def organize_by_event(self, data):
        """
        Organize flat data into REDCap's longitudinal format
        with redcap_event_name field to indicate the event
        """
        longitudinal_data = []
        
        # Group data by record ID
        record_groups = {}
        for record in data:
            record_id = record.get('record_id')
            if record_id not in record_groups:
                record_groups[record_id] = []
            record_groups[record_id].append(record)
        
        # Process each record group
        for record_id, records in record_groups.items():
            # Sort records by visit date if available
            if 'visit_date' in records[0]:
                records.sort(key=lambda r: r['visit_date'])
            
            # Map records to events
            for i, record in enumerate(records):
                # Determine which event this record belongs to
                event_name = self._determine_event(record, i)
                
                # Create the longitudinal record
                longitudinal_record = record.copy()
                longitudinal_record['redcap_event_name'] = event_name
                
                # Only include fields that are valid for this event
                event_fields = self.event_mappings.get(event_name, {}).get('fields', [])
                if event_fields:
                    for field in list(longitudinal_record.keys()):
                        if field not in event_fields and field != 'record_id' and field != 'redcap_event_name':
                            del longitudinal_record[field]
                
                longitudinal_data.append(longitudinal_record)
        
        logger.info(f"Organized {len(data)} records into {len(longitudinal_data)} event-specific records")
        return longitudinal_data
    
    def _determine_event(self, record, visit_index):
        """
        Determine which event a record belongs to based on data or index
        """
        # If record has explicit event information, use that
        if 'event_name' in record:
            return record['event_name']
        
        if 'visit_type' in record:
            visit_type = record['visit_type'].lower()
            # Map visit type to event name
            if 'baseline' in visit_type or 'screening' in visit_type:
                return 'baseline_arm_1'
            elif 'follow' in visit_type and ('3' in visit_type or 'three' in visit_type):
                return 'month_3_arm_1'
            elif 'follow' in visit_type and ('6' in visit_type or 'six' in visit_type):
                return 'month_6_arm_1'
            elif 'follow' in visit_type and ('12' in visit_type or 'twelve' in visit_type):
                return 'month_12_arm_1'
        
        # Fall back to index-based assignment using event keys in order
        event_keys = list(self.event_mappings.keys())
        if visit_index < len(event_keys):
            return event_keys[visit_index]
        else:
            return event_keys[-1]  # Assign to last event if out of range

def run_longitudinal_migration():
    """Run a longitudinal data migration to REDCap"""
    
    # Configuration - replace with your actual values
    source_file = "data/sample_longitudinal_study.csv"
    mapping_file = "../templates/longitudinal_to_redcap.json"
    redcap_url = "https://redcap.example.edu/api/"
    api_key = "YOUR_API_KEY"  # Replace with your actual API key
    
    # Event mappings for longitudinal project
    event_mappings = {
        "baseline_arm_1": {
            "fields": ["record_id", "enrollment_date", "demographics_complete", 
                      "first_name", "last_name", "dob", "gender", "contact_info_complete"]
        },
        "month_3_arm_1": {
            "fields": ["record_id", "visit_date", "weight", "height", "bmi", 
                      "bp_systolic", "bp_diastolic", "physical_exam_complete"]
        },
        "month_6_arm_1": {
            "fields": ["record_id", "visit_date", "weight", "height", "bmi", 
                      "bp_systolic", "bp_diastolic", "lab_results", "physical_exam_complete"]
        },
        "month_12_arm_1": {
            "fields": ["record_id", "visit_date", "weight", "height", "bmi", 
                      "bp_systolic", "bp_diastolic", "lab_results", "study_completion", 
                      "completion_date", "physical_exam_complete", "completion_complete"]
        }
    }
    
    logger.info("Starting longitudinal migration example")
    logger.info(f"Source: {source_file}")
    logger.info(f"Target: {redcap_url}")
    
    # Create output directory for reports
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize components
        security = SecurityHandler(secure_mode=True)  # Secure mode for PHI
        mapper = DataMapper(mapping_file)
        
        # Load validation rules from mapping file
        with open(mapping_file, 'r') as f:
            mapping_config = json.load(f)
        validation_rules = mapping_config.get("validation_rules", {})
        
        validator = DataValidator(validation_rules)
        migrator = DataMigrator(redcap_url, api_key, batch_size=25)  # Smaller batch size for complex data
        reporter = MigrationReporter(output_dir=output_dir)
        
        # Initialize longitudinal handler
        longitudinal_handler = LongitudinalDataHandler(event_mappings)
        
        # Step 1: Load source data
        logger.info("Loading source data...")
        source_data = security.load_and_secure_data(source_file)
        logger.info(f"Loaded {len(source_data)} records from source")
        
        # Step 2: Map data to REDCap format
        logger.info("Mapping data to REDCap format...")
        mapped_data = mapper.map_data(source_data)
        
        # Step 3: Organize into longitudinal structure
        logger.info("Organizing data into longitudinal structure...")
        longitudinal_data = longitudinal_handler.organize_by_event(mapped_data)
        
        # Step 4: Validate data
        logger.info("Validating data...")
        validation_results = validator.validate(longitudinal_data)
        reporter.report_validation_results(validation_results)
        
        if not validation_results['is_valid']:
            logger.error("Validation failed. Please check the validation report.")
            return
        
        # Step 5: Test connection to REDCap
        logger.info("Testing connection to REDCap...")
        connection_test = migrator.test_connection()
        if not connection_test['success']:
            logger.error(f"Failed to connect to REDCap: {connection_test.get('message', 'Unknown error')}")
            return
        
        # Step 6: Perform migration
        logger.info("Performing migration...")
        migration_result = migrator.migrate(longitudinal_data)
        
        # Step 7: Report results
        reporter.report_migration_results(migration_result)
        
        # Step 8: Generate a summary by event
        event_summary = summarize_by_event(longitudinal_data)
        summary_file = os.path.join(output_dir, f"event_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        event_summary.to_csv(summary_file, index=False)
        logger.info(f"Event summary saved to {summary_file}")
        
        # Overall summary
        success_rate = migration_result['success_rate']
        logger.info(f"Migration completed with {success_rate:.2f}% success rate")
        logger.info(f"Reports saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

def summarize_by_event(longitudinal_data):
    """Create a summary of records by event"""
    event_counts = {}
    record_counts = {}
    
    for record in longitudinal_data:
        event = record.get('redcap_event_name', 'unknown')
        record_id = record.get('record_id', 'unknown')
        
        if event not in event_counts:
            event_counts[event] = 0
        event_counts[event] += 1
        
        if record_id not in record_counts:
            record_counts[record_id] = set()
        record_counts[record_id].add(event)
    
    # Count how many records have data for each event
    unique_records_per_event = {}
    for event in event_counts.keys():
        unique_records_per_event[event] = sum(1 for record_events in record_counts.values() if event in record_events)
    
    # Create DataFrame for summary
    summary = pd.DataFrame({
        'Event': list(event_counts.keys()),
        'Total Records': [event_counts[event] for event in event_counts],
        'Unique Participants': [unique_records_per_event[event] for event in event_counts]
    })
    
    return summary

if __name__ == "__main__":
    run_longitudinal_migration()