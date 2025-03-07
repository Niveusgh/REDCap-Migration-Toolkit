"""
Data Migrator Module
Handles the actual migration of data to REDCap
"""

import json
import logging
import time
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class DataMigrator:
    """
    Handles the migration of data to REDCap via the API
    """
    
    def __init__(self, redcap_url, api_key, batch_size=100):
        """Initialize migrator with REDCap API settings"""
        self.redcap_url = redcap_url
        self.api_key = api_key
        self.batch_size = batch_size
        logger.info(f"Initialized migrator with batch size {batch_size}")
    
    def migrate(self, data, import_format="json", overwrite_behavior="overwrite"):
        """
        Migrate data to REDCap
        Returns a dictionary with migration results
        """
        if not data:
            return {"success": False, "message": "No data provided for migration"}
        
        logger.info(f"Starting migration of {len(data)} records")
        
        # Prepare result structure
        results = {
            "start_time": datetime.now().isoformat(),
            "records_processed": 0,
            "records_success": 0,
            "records_failed": 0,
            "batches_processed": 0,
            "batches_success": 0,
            "batches_failed": 0,
            "failed_records": [],
            "success": True,
            "success_rate": 0,
            "end_time": None,
            "elapsed_seconds": 0
        }
        
        # Process data in batches
        batches = self._create_batches(data, self.batch_size)
        total_batches = len(batches)
        
        logger.info(f"Processing {total_batches} batches")
        
        start_time = time.time()
        
        try:
            for i, batch in enumerate(batches):
                batch_num = i + 1
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} records)")
                
                results["batches_processed"] += 1
                records_processed = len(batch)
                results["records_processed"] += records_processed
                
                try:
                    batch_result = self._send_batch_to_redcap(batch, import_format, overwrite_behavior)
                    
                    if batch_result["success"]:
                        results["records_success"] += records_processed
                        results["batches_success"] += 1
                        logger.info(f"Batch {batch_num} successful: {records_processed} records imported")
                    else:
                        results["records_failed"] += records_processed
                        results["batches_failed"] += 1
                        failed_record_ids = [r.get("record_id", f"Record_Index_{batch.index(r)}") for r in batch]
                        results["failed_records"].extend(failed_record_ids)
                        logger.error(f"Batch {batch_num} failed: {batch_result['message']}")
                        
                except Exception as e:
                    results["records_failed"] += records_processed
                    results["batches_failed"] += 1
                    failed_record_ids = [r.get("record_id", f"Record_Index_{batch.index(r)}") for r in batch]
                    results["failed_records"].extend(failed_record_ids)
                    logger.error(f"Error processing batch {batch_num}: {str(e)}")
        
        except Exception as e:
            results["success"] = False
            logger.error(f"Migration failed: {str(e)}")
        
        # Calculate final statistics
        end_time = time.time()
        results["end_time"] = datetime.now().isoformat()
        results["elapsed_seconds"] = round(end_time - start_time, 2)
        
        if results["records_processed"] > 0:
            results["success_rate"] = (results["records_success"] / results["records_processed"]) * 100
        
        results["success"] = results["batches_failed"] == 0
        
        logger.info(f"Migration complete: {results['records_success']} of {results['records_processed']} records migrated successfully")
        return results
    
    def _create_batches(self, data, batch_size):
        """Split data into batches for processing"""
        return [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
    
    def _send_batch_to_redcap(self, batch, import_format, overwrite_behavior):
        """Send a batch of records to REDCap"""
        try:
            # Format data for REDCap API
            data_str = json.dumps(batch)
            
            # Prepare API request
            data = {
                'token': self.api_key,
                'content': 'record',
                'format': 'json',
                'type': 'flat',
                'data': data_str,
                'overwriteBehavior': overwrite_behavior,
                'returnContent': 'count',
                'returnFormat': 'json'
            }
            
            # Make API request
            response = requests.post(self.redcap_url, data=data)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict) and 'count' in result:
                    return {"success": True, "count": result['count']}
                else:
                    return {"success": True, "count": len(batch)}
            else:
                error_message = response.text
                logger.error(f"REDCap API error: {error_message}")
                return {"success": False, "message": f"API error: {error_message}"}
                
        except Exception as e:
            logger.error(f"Error sending data to REDCap: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def test_connection(self):
        """Test connection to REDCap API"""
        try:
            # Prepare API request to get project info
            data = {
                'token': self.api_key,
                'content': 'project',
                'format': 'json',
                'returnFormat': 'json'
            }
            
            # Make API request
            response = requests.post(self.redcap_url, data=data)
            
            # Check response
            if response.status_code == 200:
                project_info = response.json()
                logger.info(f"Successfully connected to REDCap project: {project_info.get('project_title', 'Unknown')}")
                return {"success": True, "project_info": project_info}
            else:
                error_message = response.text
                logger.error(f"Failed to connect to REDCap: {error_message}")
                return {"success": False, "message": error_message}
                
        except Exception as e:
            logger.error(f"Error testing connection to REDCap: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def get_data_dictionary(self):
        """Retrieve the data dictionary from REDCap"""
        try:
            # Prepare API request
            data = {
                'token': self.api_key,
                'content': 'metadata',
                'format': 'json',
                'returnFormat': 'json'
            }
            
            # Make API request
            response = requests.post(self.redcap_url, data=data)
            
            # Check response
            if response.status_code == 200:
                return {"success": True, "data_dictionary": response.json()}
            else:
                error_message = response.text
                logger.error(f"Failed to retrieve data dictionary: {error_message}")
                return {"success": False, "message": error_message}
                
        except Exception as e:
            logger.error(f"Error retrieving data dictionary: {str(e)}")
            return {"success": False, "message": str(e)}