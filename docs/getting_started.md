# Getting Started with REDCap Data Migration Toolkit

This guide will help you set up and run your first migration using the REDCap Data Migration Toolkit.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/redcap-migration-toolkit.git
   cd redcap-migration-toolkit
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Basic Usage

### 1. Prepare Your Mapping Template

Create a mapping template that defines how your source data maps to REDCap fields. You can use one of the provided templates as a starting point:

- `templates/csv_to_redcap.json` - For CSV source data
- `templates/excel_to_redcap.json` - For Excel source data

Customize the template to match your specific data fields and requirements. The basic structure is:

```json
{
  "source_type": "csv",
  "record_id_field": "participant_id",
  "fields": [
    {
      "source_field": "source_column_name",
      "target_field": "redcap_field_name",
      "field_type": "text"
    },
    // Additional field mappings...
  ]
}
```

### 2. Create a Configuration File

Create a configuration file (e.g., `config.json`) with validation rules and migration settings:

```json
{
  "validation_rules": {
    "required_fields": ["record_id", "enrollment_date"],
    "date_range": {
      "enrollment_date": {"min": "2010-01-01", "max": "2025-12-31"}
    }
  },
  "migration_settings": {
    "batch_size": 100,
    "import_format": "json"
  }
}
```

### 3. Run Data Validation

Before performing the actual migration, validate your data to identify any issues:

```
python migrate.py --config config.json --source data.csv --mapping templates/csv_to_redcap.json --redcap-url https://redcap.example.edu/api/ --api-key YOUR_API_KEY --validate-only
```

This will check your data against the validation rules and report any problems.

### 4. Perform the Migration

Once validation passes, run the full migration:

```
python migrate.py --config config.json --source data.csv --mapping templates/csv_to_redcap.json --redcap-url https://redcap.example.edu/api/ --api-key YOUR_API_KEY
```

### 5. Review Results

After the migration completes, review the log file generated in the current directory. It contains detailed information about the migration process, including any warnings or errors.

## Example Workflow

For a visual representation of the migration process, see the [example workflow diagram](example_workflow.png).

## Next Steps

- Read the [Best Practices](best_practices.md) guide for tips on optimizing your migrations
- Explore the template examples to understand different mapping scenarios
- Check out the example scripts in the `examples/` directory for more complex use cases

## Troubleshooting

If you encounter issues during migration:

1. Check the log file for specific error messages
2. Ensure your mapping template correctly matches your source data structure
3. Verify your REDCap API URL and key have appropriate permissions
4. For PHI data, make sure to use the `--secure-mode` flag to enable enhanced security features