"""
Data Mapper Module
Maps data from legacy formats to REDCap-compatible structure
"""

import json
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataMapper:
    """
    Maps source data to REDCap format based on mapping template
    """
    
    def __init__(self, mapping_file):
        """Initialize mapper with mapping configuration"""
        self.mapping = self._load_mapping(mapping_file)
        logger.info(f"Loaded mapping with {len(self.mapping['fields'])} field definitions")
    
    def _load_mapping(self, mapping_file):
        """Load and validate mapping template from file"""
        try:
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
            
            # Validate mapping structure
            required_keys = ['fields', 'source_type', 'record_id_field']
            for key in required_keys:
                if key not in mapping:
                    raise ValueError(f"Mapping template missing required key: {key}")
            
            return mapping
        except Exception as e:
            logger.error(f"Failed to load mapping file: {e}")
            raise
    
    def map_data(self, source_data):
        """Map source data to REDCap format"""
        logger.info("Starting data mapping process")
        
        try:
            # Convert to pandas DataFrame if not already
            if not isinstance(source_data, pd.DataFrame):
                if self.mapping['source_type'] == 'csv':
                    source_data = pd.DataFrame(source_data)
                else:
                    raise ValueError(f"Unsupported source data type for automatic conversion")
            
            # Create empty result structure
            redcap_data = []
            
            # Process each record
            for _, row in source_data.iterrows():
                record = {}
                
                # Set record ID
                src_id_field = self.mapping['record_id_field']
                if src_id_field in row:
                    record['record_id'] = str(row[src_id_field])
                else:
                    logger.warning(f"Record ID field '{src_id_field}' not found in source data")
                    continue
                
                # Map each field according to mapping definition
                for field_map in self.mapping['fields']:
                    self._map_field(field_map, row, record)
                
                redcap_data.append(record)
            
            logger.info(f"Mapped {len(redcap_data)} records successfully")
            return redcap_data
            
        except Exception as e:
            logger.error(f"Error during data mapping: {e}")
            raise
    
    def _map_field(self, field_map, source_row, target_record):
        """Map a single field based on its mapping definition"""
        source_field = field_map.get('source_field')
        target_field = field_map.get('target_field')
        field_type = field_map.get('field_type', 'text')
        
        # Skip if source field not in data
        if source_field not in source_row:
            logger.debug(f"Source field '{source_field}' not found, skipping")
            return
        
        # Get raw value
        value = source_row[source_field]
        
        # Apply transformations based on field type
        if field_type == 'date':
            value = self._format_date(value, field_map.get('date_format'))
        elif field_type == 'checkbox':
            value = self._format_checkbox(value, field_map.get('options', {}))
        elif field_type == 'radio':
            value = self._format_radio(value, field_map.get('options', {}))
        elif field_type == 'dropdown':
            value = self._format_dropdown(value, field_map.get('options', {}))
        elif field_type == 'calculated':
            value = self._apply_calculation(source_row, field_map.get('formula'))
        
        # Set value in target record
        target_record[target_field] = value
    
    def _format_date(self, value, date_format=None):
        """Format date values to REDCap's expected format"""
        if pd.isna(value) or value == '':
            return ''
        
        try:
            if date_format:
                dt = datetime.strptime(str(value), date_format)
            else:
                # Try common formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y']:
                    try:
                        dt = datetime.strptime(str(value), fmt)
                        break
                    except ValueError:
                        continue
                else:
                    logger.warning(f"Could not parse date value: {value}")
                    return value
            
            # Return in REDCap's preferred format (YYYY-MM-DD)
            return dt.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Error formatting date {value}: {e}")
            return value
    
    def _format_checkbox(self, value, options):
        """Format checkbox values for REDCap"""
        result = {}
        if pd.isna(value):
            return result
        
        # Handle different source formats
        if isinstance(value, str):
            values = [v.strip() for v in value.split(',')]
        elif isinstance(value, (list, tuple)):
            values = value
        else:
            values = [value]
        
        # Map to REDCap checkbox format
        for code, label in options.items():
            result[code] = '1' if label in values or code in values else '0'
        
        return result
    
    def _format_radio(self, value, options):
        """Format radio button values for REDCap"""
        if pd.isna(value) or value == '':
            return ''
        
        # Try to find the code for this value
        for code, label in options.items():
            if label == value or code == value:
                return code
        
        logger.warning(f"Radio value '{value}' not found in options")
        return ''
    
    def _format_dropdown(self, value, options):
        """Format dropdown values for REDCap (same as radio)"""
        return self._format_radio(value, options)
    
    def _apply_calculation(self, row, formula):
        """Apply a simple calculation to the data"""
        if not formula:
            return ''
            
        try:
            # Replace field references with values
            for field in row.index:
                if f'{{{field}}}' in formula:
                    formula = formula.replace(f'{{{field}}}', str(row[field]))
            
            # Evaluate the expression
            return str(eval(formula))
        except Exception as e:
            logger.warning(f"Error in calculation: {e}")
            return ''