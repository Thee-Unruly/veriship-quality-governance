# VeriShip Automated Test Runner

Automatically execute all your test cases and generate reports without manually clicking through the UI.

## How It Works

The automation script:
1. Fetches all test cases from your backend
2. Executes each test sequentially using your Playwright configuration
3. Collects results and metrics
4. Generates HTML and JSON reports
5. Displays a summary in the console

## Installation

The script uses `axios` which should already be installed. If not:

```bash
npm install axios
```

## Usage

### Manual Execution

Run all tests for a project:
```bash
node automation-runner.js 1
```

Run tests and generate HTML/JSON reports:
```bash
node automation-runner.js 1 --report
```

Run tests, generate reports, and send email:
```bash
node automation-runner.js 1 --report --email
```

### Via npm Scripts

```bash
npm run test:auto           # Run tests and generate reports
npm run test:auto:email     # Run tests, generate reports, and email
```

## Scheduling Tests

### Option 1: Windows Task Scheduler

1. Create a batch file `run-tests.bat`:
```batch
@echo off
cd C:\Users\ibrahim.fadhili\Videos\VeriShip\veriship-quality-governance
npm run test:auto
```

2. Open Task Scheduler:
   - Create Basic Task
   - Set trigger (daily, weekly, etc.)
   - Set action: Run `run-tests.bat`
   - Check "Run whether user is logged in or not"

### Option 2: cron (Linux/Mac)

Add to your crontab:
```bash
# Run tests every day at 2 AM
0 2 * * * cd /path/to/veriship && npm run test:auto
```

### Option 3: GitHub Actions

Create `.github/workflows/automated-tests.yml`:
```yaml
name: Automated Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run test:auto
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-reports
          path: test-reports/
```

## Reports

### HTML Report
- Visual summary with charts
- Pass/fail breakdown
- Test duration and steps
- Located in: `test-reports/test-report-{timestamp}.html`

### JSON Report
- Machine-readable results
- Can be integrated with other tools
- Located in: `test-reports/test-report-{timestamp}.json`

## Configuration

Edit the script to change default settings:

```javascript
const DEFAULT_CONFIG = {
  browser_type: 'chromium',      // chromium, firefox, webkit
  headless: true,                // Run in headless mode
  viewport: { width: 1280, height: 720 },
  timeout: 30000,                // 30 seconds
  base_url: 'http://localhost:3000',
  record_trace: true,            // Record execution trace
  screenshot_on_failure: true,
  retry_count: 0,
  environment: 'development',
};
```

## Your UI vs Automation

| Feature | UI | Automation Script |
|---------|----|--------------------|
| **Manual testing** | ✓ | |
| **Debugging** | ✓ | |
| **View results visually** | ✓ | ✓ (Reports) |
| **Run on schedule** | | ✓ |
| **Unattended execution** | | ✓ |
| **Generate reports** | | ✓ |
| **CI/CD integration** | | ✓ |
| **Run all tests at once** | | ✓ |

## Example Workflow

1. **Development**: Use the Playwright UI page to test individual test cases
2. **Before commit**: Run `npm run test:auto` to verify all tests pass
3. **Scheduled**: Set up Windows Task Scheduler to run tests nightly
4. **CI/CD**: Add GitHub Actions to run tests on every push

## Troubleshooting

**Script can't connect to backend:**
- Make sure your backend is running: `python run.py`
- Check `API_BASE_URL` in the script matches your backend URL

**Tests timing out:**
- Increase `timeout` in `DEFAULT_CONFIG`
- Check your application is responsive

**Reports not generating:**
- Make sure `test-reports/` directory exists
- Check write permissions on the directory

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed
- Useful for CI/CD pipelines to determine if deployment should continue
