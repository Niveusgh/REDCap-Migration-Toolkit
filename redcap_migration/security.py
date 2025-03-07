"""
Security Handler Module
Manages security aspects of data migration, including PHI protection
"""

import logging
import os
import json
import csv
import pandas as pd
import re
from datetime import datetime
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class SecurityHandler:
    """
    Handles security concerns during data migration, including PHI identification and protection
    """
    
    def __init__(self, secure_mode=False, phi_fields=None):
        """Initialize security handler"""
        self.secure_mode = secure_mode
        self.phi_fields = phi_fields or []
        self.temp_files = []
        
        # Generate encryption key if in secure mode
        if secure_mode:
            self.encryption_key = Fernet.generate_key()
            self.cipher = Fernet(self.encryption_key)
            logger.info("Initialized security handler in secure mode with encryption")
        else:
            self.encryption_key = None
            self.cipher = None
            logger.info("Initialized security handler in standard mode")
    
    def load_and_secure_data(self, source_path):
        """
        Load data from source file with appropriate security measures
        Supports CSV, Excel, and JSON formats
        """
        logger.info(f"Loading data from {source_path}")
        
        file_ext = os.path.splitext(source_path)[1].lower()
        
        try:
            if file_ext == '.csv':
                data = self._load_csv(source_path)
            elif file_ext in ['.xls', '.xlsx']:
                data = self._load_excel(source_path)
            elif file_ext == '.json':
                data = self._load_json(source_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            logger.info(f"Successfully loaded {len(data)} records from {source_path}")
            
            # Apply security measures if in secure mode
            if self.secure_mode:
                data = self._secure_phi_data(data)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            raise
    
    def _load_csv(self, filepath):
        """Load data from CSV file"""
        try:
            df = pd.read_csv(filepath)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            raise
    
    def _load_excel(self, filepath):
        """Load data from Excel file"""
        try:
            df = pd.read_excel(filepath)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            raise
    
    def _load_json(self, filepath):
        """Load data from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data if isinstance(data, list) else [data]
        except Exception as e:
            logger.error(f"Error loading JSON file: {str(e)}")
            raise
    
    def _secure_phi_data(self, data):
        """Apply security measures to PHI fields in the data"""
        if not self.phi_fields:
            # If no PHI fields specified, try to automatically detect them
            self.phi_fields = self._detect_phi_fields(data)
            logger.info(f"Automatically detected potential PHI fields: {', '.join(self.phi_fields)}")
        
        secured_data = []
        for record in data:
            secured_record = record.copy()
            
            for field in self.phi_fields:
                if field in secured_record and secured_record[field]:
                    # Encrypt PHI fields if encryption is enabled
                    if self.cipher:
                        original_value = str(secured_record[field])
                        encrypted_value = self.cipher.encrypt(original_value.encode()).decode()
                        secured_record[f"{field}_encrypted"] = encrypted_value
                        secured_record[field] = self._redact_phi(original_value)
                    else:
                        # Otherwise just redact the data
                        secured_record[field] = self._redact_phi(str(secured_record[field]))
            
            secured_data.append(secured_record)
        
        logger.info(f"Applied security measures to {len(self.phi_fields)} PHI fields")
        return secured_data
    
    def _detect_phi_fields(self, data):
        """
        Attempt to automatically detect fields that might contain PHI
        This is a simple heuristic and should be supplemented with manual review
        """
        if not data or len(data) == 0:
            return []
        
        # Sample record for field detection
        sample_record = data[0]
        potential_phi_fields = []
        
        # Common PHI field names
        phi_field_patterns = [
            r'(?i)(name|first|last|middle|initial|full)',
            r'(?i)(ssn|social|security)',
            r'(?i)(dob|birth|birthday)',
            r'(?i)(address|street|city|state|zip|postal)',
            r'(?i)(email|e-mail)',
            r'(?i)(phone|cell|mobile|fax)',
            r'(?i)(mrn|medical|record|patient|id)',
            r'(?i)(license|driver)',
        ]
        
        # Check field names against patterns
        for field in sample_record.keys():
            for pattern in phi_field_patterns:
                if re.search(pattern, field):
                    potential_phi_fields.append(field)
                    break
        
        return potential_phi_fields
    
    def _redact_phi(self, value):
        """Redact PHI data for secure display"""
        if not value:
            return value
            
        # Handle different data types
        if '@' in value and '.' in value.split('@')[1]:  # Email
            parts = value.split('@')
            username = parts[0][0] + '*' * (len(parts[0]) - 2) + parts[0][-1] if len(parts[0]) > 2 else '*' * len(parts[0])
            domain = parts[1]
            return f"{username}@{domain}"
        
        elif re.match(r'^[0-9-()]+$', value):  # Phone number
            # Keep first and last digits, replace middle with asterisks
            clean_digits = re.sub(r'[^0-9]', '', value)
            if len(clean_digits) > 4:
                return clean_digits[0:2] + '*' * (len(clean_digits) - 4) + clean_digits[-2:]
            else:
                return '*' * len(clean_digits)
        
        elif len(value) > 6:  # General text, could be name or address
            return value[0:2] + '*' * (len(value) - 4) + value[-2:]
        
        else:  # Short values
            return '*' * len(value)
    
    def decrypt_field(self, encrypted_value):
        """Decrypt an encrypted field value"""
        if not self.cipher:
            raise ValueError("Encryption not initialized")
            
        try:
            return self.cipher.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error(f"Error decrypting value: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up any temporary files created during processing"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {str(e)}")
                
        self.temp_files = []
    
    def generate_phi_report(self, data):
        """Generate a report on PHI fields in the data"""
        if not data:
            return {"phi_fields": [], "phi_counts": {}}
        
        phi_counts = {field: 0 for field in self.phi_fields}
        records_with_phi = 0
        
        for record in data:
            has_phi = False
            for field in self.phi_fields:
                if field in record and record[field]:
                    phi_counts[field] += 1
                    has_phi = True
            
            if has_phi:
                records_with_phi += 1
        
        return {
            "phi_fields": self.phi_fields,
            "phi_counts": phi_counts,
            "records_with_phi": records_with_phi,
            "total_records": len(data),
            "phi_percentage": (records_with_phi / len(data) * 100) if data else 0
        }
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()