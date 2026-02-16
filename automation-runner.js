#!/usr/bin/env node

/**
 * VeriShip Automated Test Runner
 * Executes all test cases via the backend API and generates a report
 * Usage: node automation-runner.js [projectId] [--report] [--email]
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000/api';
const REPORT_DIR = path.join(__dirname, 'test-reports');
const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-');

// Default Playwright config
const DEFAULT_CONFIG = {
    browser_type: 'chromium',
    headless: true,
    viewport: { width: 1280, height: 720 },
    timeout: 30000,
    base_url: 'http://localhost:3000',
    record_trace: true,
    record_video: false,
    screenshot_on_failure: true,
    retry_count: 0,
    environment: 'development',
};

// Create reports directory if it doesn't exist
if (!fs.existsSync(REPORT_DIR)) {
    fs.mkdirSync(REPORT_DIR, { recursive: true });
}

/**
 * Fetch all test cases for a project
 */
async function fetchTestCases(projectId) {
    try {
        console.log(`📋 Fetching test cases for project ${projectId}...`);
        const response = await axios.get(`${API_BASE_URL}/test-cases/${projectId}`);
        console.log(`✓ Found ${response.data.length} test cases`);
        return response.data;
    } catch (error) {
        console.error('❌ Error fetching test cases:', error.message);
        return [];
    }
}

/**
 * Execute a single test case
 */
async function executeTestCase(testCaseId, config = DEFAULT_CONFIG) {
    try {
        const response = await axios.post(
            `${API_BASE_URL}/automation/execute/test-case/${testCaseId}?executed_by=automation`,
            config,
            { timeout: 120000 } // 2 minute timeout for execution
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return {
            success: false,
            error: error.response?.data?.detail || error.message,
        };
    }
}

/**
 * Run all test cases sequentially
 */
async function runAllTests(projectId, testCases) {
    console.log(`\n🚀 Starting test execution for ${testCases.length} test cases...\n`);

    const results = {
        totalTests: testCases.length,
        passed: 0,
        failed: 0,
        skipped: 0,
        startTime: new Date(),
        endTime: null,
        testResults: [],
    };

    for (let i = 0; i < testCases.length; i++) {
        const tc = testCases[i];
        const testNum = i + 1;
        process.stdout.write(`[${testNum}/${testCases.length}] Testing "${tc.title}"... `);

        const startTime = Date.now();
        const result = await executeTestCase(tc.id, DEFAULT_CONFIG);
        const duration = Date.now() - startTime;

        if (result.success) {
            const status = result.data.status;
            if (status === 'passed') {
                console.log(`✓ PASSED (${duration}ms)`);
                results.passed++;
            } else if (status === 'failed') {
                console.log(`✗ FAILED (${duration}ms)`);
                results.failed++;
            } else {
                console.log(`⊘ SKIPPED (${duration}ms)`);
                results.skipped++;
            }
            results.testResults.push({
                testCaseId: tc.id,
                testCaseTitle: tc.title,
                status,
                duration,
                executionId: result.data.execution_id,
                steps: result.data.steps.length,
                error: result.data.error_message,
            });
        } else {
            console.log(`✗ ERROR: ${result.error}`);
            results.failed++;
            results.testResults.push({
                testCaseId: tc.id,
                testCaseTitle: tc.title,
                status: 'error',
                duration,
                error: result.error,
            });
        }

        // Add small delay between tests
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    results.endTime = new Date();
    results.totalDuration = (results.endTime - results.startTime) / 1000;

    return results;
}

/**
 * Generate HTML report
 */
function generateHTMLReport(results, projectId) {
    const passRate = ((results.passed / results.totalTests) * 100).toFixed(1);
    const reportFile = path.join(REPORT_DIR, `test-report-${TIMESTAMP}.html`);

    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VeriShip Test Report</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 8px; margin-bottom: 30px; }
    .header h1 { font-size: 32px; margin-bottom: 10px; }
    .header p { opacity: 0.9; font-size: 16px; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
    .summary-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .summary-card h3 { color: #666; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }
    .summary-card .value { font-size: 32px; font-weight: bold; }
    .summary-card.passed .value { color: #10b981; }
    .summary-card.failed .value { color: #ef4444; }
    .summary-card.skipped .value { color: #f59e0b; }
    .results { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .results-header { background: #f9fafb; padding: 20px; border-bottom: 1px solid #e5e7eb; }
    .results-header h2 { font-size: 18px; }
    .test-row { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 20px; padding: 15px 20px; border-bottom: 1px solid #f3f4f6; align-items: center; }
    .test-row:last-child { border-bottom: none; }
    .test-row.header { background: #f9fafb; font-weight: bold; font-size: 12px; text-transform: uppercase; color: #666; }
    .test-name { font-weight: 500; }
    .status { padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600; text-align: center; }
    .status.passed { background: #d1fae5; color: #065f46; }
    .status.failed { background: #fee2e2; color: #991b1b; }
    .status.error { background: #fee2e2; color: #991b1b; }
    .status.skipped { background: #fef3c7; color: #92400e; }
    .footer { margin-top: 40px; text-align: center; color: #666; font-size: 12px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🧪 Test Execution Report</h1>
      <p>Project ID: ${projectId} | ${results.startTime.toLocaleString()}</p>
    </div>

    <div class="summary">
      <div class="summary-card">
        <h3>Total Tests</h3>
        <div class="value">${results.totalTests}</div>
      </div>
      <div class="summary-card passed">
        <h3>Passed</h3>
        <div class="value">${results.passed}</div>
      </div>
      <div class="summary-card failed">
        <h3>Failed</h3>
        <div class="value">${results.failed}</div>
      </div>
      <div class="summary-card skipped">
        <h3>Skipped</h3>
        <div class="value">${results.skipped}</div>
      </div>
      <div class="summary-card">
        <h3>Pass Rate</h3>
        <div class="value">${passRate}%</div>
      </div>
      <div class="summary-card">
        <h3>Total Duration</h3>
        <div class="value">${results.totalDuration.toFixed(1)}s</div>
      </div>
    </div>

    <div class="results">
      <div class="results-header">
        <h2>Test Results</h2>
      </div>
      <div class="test-row header">
        <div>Test Case</div>
        <div>Status</div>
        <div>Duration</div>
        <div>Steps</div>
      </div>
      ${results.testResults.map(tr => `
        <div class="test-row">
          <div class="test-name">${tr.testCaseTitle}</div>
          <div><span class="status ${tr.status}">${tr.status.toUpperCase()}</span></div>
          <div>${tr.duration}ms</div>
          <div>${tr.steps || 'N/A'}</div>
        </div>
      `).join('')}
    </div>

    <div class="footer">
      <p>Report generated on ${new Date().toLocaleString()}</p>
      <p>VeriShip Quality Governance Platform</p>
    </div>
  </div>
</body>
</html>
  `;

    fs.writeFileSync(reportFile, html);
    console.log(`\n📊 Report saved to: ${reportFile}`);
    return reportFile;
}

/**
 * Generate JSON report
 */
function generateJSONReport(results, projectId) {
    const reportFile = path.join(REPORT_DIR, `test-report-${TIMESTAMP}.json`);
    const report = {
        projectId,
        timestamp: new Date().toISOString(),
        summary: {
            totalTests: results.totalTests,
            passed: results.passed,
            failed: results.failed,
            skipped: results.skipped,
            passRate: ((results.passed / results.totalTests) * 100).toFixed(1),
            totalDuration: results.totalDuration,
        },
        testResults: results.testResults,
    };

    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
    console.log(`📄 JSON report saved to: ${reportFile}`);
    return reportFile;
}

/**
 * Print summary to console
 */
function printSummary(results) {
    const passRate = ((results.passed / results.totalTests) * 100).toFixed(1);

    console.log('\n' + '='.repeat(60));
    console.log('📊 TEST EXECUTION SUMMARY');
    console.log('='.repeat(60));
    console.log(`Total Tests:    ${results.totalTests}`);
    console.log(`✓ Passed:       ${results.passed}`);
    console.log(`✗ Failed:       ${results.failed}`);
    console.log(`⊘ Skipped:      ${results.skipped}`);
    console.log(`Pass Rate:      ${passRate}%`);
    console.log(`Duration:       ${results.totalDuration.toFixed(1)}s`);
    console.log('='.repeat(60) + '\n');

    if (results.failed > 0) {
        console.log('❌ Failed Tests:');
        results.testResults
            .filter(tr => tr.status === 'failed' || tr.status === 'error')
            .forEach(tr => {
                console.log(`  - ${tr.testCaseTitle}`);
                if (tr.error) console.log(`    Error: ${tr.error}`);
            });
        console.log();
    }
}

/**
 * Main function
 */
async function main() {
    const projectId = process.argv[2] || '1';
    const generateReport = process.argv.includes('--report');
    const sendEmail = process.argv.includes('--email');

    console.log('🚀 VeriShip Automated Test Runner\n');

    // Fetch test cases
    const testCases = await fetchTestCases(projectId);
    if (testCases.length === 0) {
        console.error('No test cases found. Exiting.');
        process.exit(1);
    }

    // Run all tests
    const results = await runAllTests(projectId, testCases);

    // Print summary
    printSummary(results);

    // Generate reports
    if (generateReport) {
        generateHTMLReport(results, projectId);
        generateJSONReport(results, projectId);
    }

    // Exit with appropriate code
    process.exit(results.failed > 0 ? 1 : 0);
}

main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});
