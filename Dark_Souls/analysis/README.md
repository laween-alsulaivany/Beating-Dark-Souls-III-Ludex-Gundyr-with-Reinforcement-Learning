# DS3 Training Data Analyzer

A comprehensive CLI tool for analyzing Dark Souls III reinforcement learning training data.

## Features

- **Data Cleaning**: Filter out invalid training episodes
- **Log Parsing**: Convert raw logs to structured CSV format  
- **Statistical Analysis**: Generate comprehensive training metrics
- **Visualization**: Create detailed plots and charts
- **Real-time Monitoring**: Monitor live game data during training

## Usage

```bash
# Clean raw log files
python ds3_analyzer.py clean run_log_model_4.txt --min-duration 10

# Parse cleaned logs to CSV
python ds3_analyzer.py parse cleaned_run_log_model_4.txt

# Generate comprehensive analysis
python ds3_analyzer.py analyze training_data.csv

# Monitor real-time game data
python ds3_analyzer.py monitor --duration 120

# List available files
python ds3_analyzer.py list
```

## Output

- **Cleaned logs**: Filtered training episodes
- **CSV data**: Structured training data with rewards
- **Analysis plots**: Comprehensive visualizations
- **Summary statistics**: Training performance metrics

All outputs are saved to the `analysis/output/` directory.
