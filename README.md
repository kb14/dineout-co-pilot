# Dineout GenAI Co-Pilot

A CLI-first prototype that generates concise, actionable reports for Sales & Account Managers to use before restaurant partner meetings.

## Features

- Generates comprehensive restaurant performance reports
- Combines metrics, ad performance, peer benchmarks, and AI recommendations
- CLI interface for quick report generation
- Markdown output format
- Model used: gpt-4o

## Setup

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Generate Reports
Generate a report for a restaurant:
```bash
python scripts/generate_report.py R001
```

### Evaluate Report Quality
Run structural evaluations on generated reports:

```bash
# Evaluate all reports in outputs/ directory
python src/evals/eval_runner.py --batch

# Evaluate specific report with detailed output
python src/evals/eval_runner.py --report outputs/R002/report.md --detailed

# Save detailed evaluation results to files
python src/evals/eval_runner.py --batch --save-results
```

Evaluation results are saved to `outputs/[RESTAURANT_ID]/evals/structural_eval.json`

## Project Structure

```
dineout-co-pilot/
│ README.md
│ requirements.txt
├─ data/               # Generated CSV data files
├─ db/                 # SQLite database for SQL Agent
├─ src/
│   ├─ loaders.py     # Data loading utilities
│   ├─ agents/        # Agents of the system
│   ├─ evals/         # Evaluation framework
│   │   ├─ evaluators/  # Different evaluation types
│   │   └─ eval_runner.py  # Main evaluation runner
│   └─ utils/         # Utility functions
├─ scripts/
│   └─ generate_report.py  # CLI entry point
├─ notebooks/         # Development notebooks
├─ outputs/          # Generated reports, charts, and artifacts
|   └─ R*/           # Individual restaurant reports
|       ├─ report.md   # Generated report
|       ├─ plots/      # Visualization charts
|       └─ evals/      # Evaluation results
```

## Data Generation Process

The data was designed maintaining realistic patterns and relationships between different aspects of restaurant performance.


### Data Files
- `restaurant_master.csv`: Restaurant metadata
- `restaurant_metrics.csv`: Daily performance metrics for last 30 days (1 row per restaurant per day)
- `ads_data.csv`: Ad campaign data with intervals within last 30 days
- `discount_history.csv`: Historical discount configurations with intervals within last 30 days
- `peer_benchmarks.csv`: Monthly average benchmarks by locality and cuisine


## Data Loading System

The system implements a dual-mode data loading approach:

### DataFrame Mode
- Fast prototyping and analysis
- Used by most agents for standard metrics

### SQLite Mode
- Enables advanced querying capabilities
- Better for large-scale data handling
- Powers complex calculations in AdsAnalyzerAgent and DiscountAnalyzerAgent where loading entire dataset into memory isn't feasible
- Supports the SQL Agent for custom analysis

## System Flow

The system follows a modular, agent-based architecture:

1. **Data Loading**
   - Load CSVs into DataFrames
   - Initialize SQLite database

2. **Agent Analysis**
   - **TrendsAgent**: Calculates recent performance metrics and generates trend visualizations
   - **AdsAnalyzerAgent**: Evaluates ad campaign effectiveness and ROI. Also, does ad campaign analysis using the SQL Agent
   - **DiscountAnalyzerAgent**: Analyzes impact of discount strategies
   - **BenchmarkAnalyzerAgent**: Compares performance against peer restaurants
   - **RecommendationsAgent**: Generates data-driven suggestions

3. **Orchestration**
   - Combines all agent outputs
   - Generates final structured report
   - Saves visualizations and artifacts

## Recommendations Agent Design

The RecommendationsAgent is intentionally constrained to mirror real-world decision-making:

- Uses predefined rules that match account manager guidelines
- Focuses on actionable metrics that restaurants can influence
- Maintains transparency in suggestion logic
- Ensures recommendations are practical and implementable

This design choice keeps suggestions aligned with business realities.

## Production & Scale Considerations

### Handling Complex Data
- Pre-generate table summaries stored in vector database
- Provide context to LLM prompts for better understanding
- Optimize agent orchestration with metadata

### Evals
- Golden dataset of manually reviewed "good reports"
- LLM judge compares generated report vs golden report (eg: "rate the clarity of trends", "does the recommendation follow account manager guidelines?")
- Basic sanity tests (eg: "does report have all sections?", "do the numbers in trend summary match with actual dataframe calculations?")
- Validation against raw DataFrame calculations to check for hallucimated numbers

### Future Features
- Asynchronous batch report generation
- Automated performance monitoring and alerting
