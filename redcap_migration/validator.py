"""
Data Validator Module
Validates data before and after migration to ensure integrity and compliance
"""

import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class DataValidator:
    """
    Validates data against rules and constraints to ensure quality and completeness
    """
    
    def __init__(self, validation_rules=None):
        """Initialize validator with validation rules"""
        self.validation_rules = validation_rules or {}
        logger.info(f"Initialized validator with {len(self.validation_rules)} rule categories")
    
    def validate(self, data):
        """
        Validate data against all rules
        Returns a dictionary with validation results
        """
        if not data:
            return {"is_valid": False, "errors": ["No data provided for validation"]}
        
        logger.info(f"Starting validation of {len(data)} records")
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "record_issues": {},
            "stats": {
                "total_records": len(data),
                "records_with_issues": 0,
                "total_errors": 0,
                "total_warnings": 0
            }
        }
        
        # Run all validation checks
        self._check_required_fields(data, results)
        self._check_field_formats(data, results)
        self._check_date_ranges(data, results)
        self._check_numeric_ranges(data, results)
        self._check_data_consistency(data, results)
        
        # Update summary statistics
        results["stats"]["records_with_issues"] = len(results["record_issues"])
        results["stats"]["total_errors"] = len(results["errors"]) + sum(
            len(issues.get("errors", [])) for issues in results["record_issues"].values()
        )
        results["stats"]["total_warnings"] = len(results["warnings"]) + sum(
            len(issues.get("warnings", [])) for issues in results["record_issues"].values()
        )
        
        # Set overall validity flag
        results["is_valid"] = results["stats"]["total_errors"] == 0
        
        logger.info(f"Validation complete: {results['stats']['total_errors']} errors, {results['stats']['total_warnings']} warnings")
        return results
    
    def _check_required_fields(self, data, results):
        """Check for required fields in each record"""
        required_fields = self.validation_rules.get("required_fields", [])
        if not required_fields:
            return
        
        for i, record in enumerate(data):
            record_id = record.get("record_id", f"Record_{i}")
            missing_fields = [field for field in required_fields if field not in record or not record[field]]
            
            if missing_fields:
                self._add_record_issue(
                    results, 
                    record_id, 
                    "errors", 
                    f"Missing required fields: {', '.join(missing_fields)}"
                )
    
    def _check_field_formats(self, data, results):
        """Check that field values match expected formats"""
        format_rules = self.validation_rules.get("field_formats", {})
        if not format_rules:
            return
        
        for i, record in enumerate(data):
            record_id = record.get("record_id", f"Record_{i}")
            
            for field, format_rule in format_rules.items():
                if field in record and record[field]:
                    value = record[field]
                    if format_rule == "date" and not self._is_valid_date(value):
                        self._add_record_issue(
                            results, 
                            record_id, 
                            "errors", 
                            f"Invalid date format in field '{field}': {value}"
                        )
                    elif format_rule == "email" and not self._is_valid_email(value):
                        self._add_record_issue(
                            results, 
                            record_id, 
                            "errors", 
                            f"Invalid email format in field '{field}': {value}"
                        )
                    elif format_rule == "phone" and not self._is_valid_phone(value):
                        self._add_record_issue(
                            results, 
                            record_id, 
                            "errors", 
                            f"Invalid phone format in field '{field}': {value}"
                        )
    
    def _check_date_ranges(self, data, results):
        """Check that date values fall within acceptable ranges"""
        date_ranges = self.validation_rules.get("date_range", {})
        if not date_ranges:
            return
        
        for i, record in enumerate(data):
            record_id = record.get("record_id", f"Record_{i}")
            
            for field, range_rule in date_ranges.items():
                if field in record and record[field]:
                    try:
                        value = record[field]
                        date_value = datetime.strptime(value, '%Y-%m-%d')
                        min_date = datetime.strptime(range_rule.get("min", "1900-01-01"), '%Y-%m-%d')
                        max_date = datetime.strptime(range_rule.get("max", "2100-12-31"), '%Y-%m-%d')
                        
                        if date_value < min_date:
                            self._add_record_issue(
                                results, 
                                record_id, 
                                "errors", 
                                f"Date in field '{field}' is before minimum allowed: {value} < {range_rule['min']}"
                            )
                        elif date_value > max_date:
                            self._add_record_issue(
                                results, 
                                record_id, 
                                "errors", 
                                f"Date in field '{field}' is after maximum allowed: {value} > {range_rule['max']}"
                            )
                    except ValueError:
                        self._add_record_issue(
                            results, 
                            record_id, 
                            "errors", 
                            f"Could not parse date in field '{field}': {value}"
                        )
    
    def _check_numeric_ranges(self, data, results):
        """Check that numeric values fall within acceptable ranges"""
        numeric_ranges = self.validation_rules.get("numeric_range", {})
        if not numeric_ranges:
            return
        
        for i, record in enumerate(data):
            record_id = record.get("record_id", f"Record_{i}")
            
            for field, range_rule in numeric_ranges.items():
                if field in record and record[field]:
                    try:
                        value = float(record[field])
                        min_val = float(range_rule.get("min", float("-inf")))
                        max_val = float(range_rule.get("max", float("inf")))
                        
                        if value < min_val:
                            self._add_record_issue(
                                results, 
                                record_id, 
                                "errors", 
                                f"Value in field '{field}' is below minimum: {value} < {min_val}"
                            )
                        elif value > max_val:
                            self._add_record_issue(
                                results, 
                                record_id, 
                                "errors", 
                                f"Value in field '{field}' is above maximum: {value} > {max_val}"
                            )
                    except ValueError:
                        self._add_record_issue(
                            results, 
                            record_id, 
                            "errors", 
                            f"Could not parse numeric value in field '{field}': {record[field]}"
                        )
    
    def _check_data_consistency(self, data, results):
        """Check for data consistency issues across records"""
        # Check for duplicate record IDs
        record_ids = [r.get("record_id") for r in data if "record_id" in r]
        duplicate_ids = set([rid for rid in record_ids if record_ids.count(rid) > 1])
        
        for dup_id in duplicate_ids:
            results["errors"].append(f"Duplicate record ID found: {dup_id}")
        
        # Check for consistent field presence across records
        all_fields = set()
        for record in data:
            all_fields.update(record.keys())
        
        for i, record in enumerate(data):
            record_id = record.get("record_id", f"Record_{i}")
            missing_fields = all_fields - set(record.keys())
            
            # Exclude record_id field from this check
            if "record_id" in missing_fields:
                missing_fields.remove("record_id")
            
            if missing_fields:
                self._add_record_issue(
                    results, 
                    record_id, 
                    "warnings", 
                    f"Fields present in other records but missing in this one: {', '.join(missing_fields)}"
                )
    
    def _add_record_issue(self, results, record_id, issue_type, message):
        """Add an issue to a specific record in the results"""
        if record_id not in results["record_issues"]:
            results["record_issues"][record_id] = {"errors": [], "warnings": []}
        
        results["record_issues"][record_id][issue_type].append(message)
    
    def _is_valid_date(self, date_str):
        """Check if a string is a valid date"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _is_valid_email(self, email):
        """Basic email validation"""
        return '@' in email and '.' in email.split('@')[1]
    
    def _is_valid_phone(self, phone):
        """Basic phone number validation"""
        digits = ''.join(c for c in phone if c.isdigit())
        return len(digits) >= 10