# AI-Powered Testing Guide

## Overview

VeriShip Quality Governance now integrates **OpenRouter API** for AI-powered test generation and failure analysis. OpenRouter provides unified access to multiple LLM models (Claude, GPT-4, Llama, Mistral, etc.) with a single API key.

## Why OpenRouter?

✅ **Multiple Models**: Access Claude, GPT-4, Llama, Mistral, and more  
✅ **Cost-Effective**: Pay-as-you-go pricing, often cheaper than direct APIs  
✅ **No Vendor Lock-in**: Easy to switch models without code changes  
✅ **Simplified Setup**: One API key instead of multiple vendor keys  
✅ **Fallback Support**: Automatically handles model availability  

## Setup Instructions

### 1. Get Your OpenRouter API Key

Visit [https://openrouter.ai](https://openrouter.ai) and:

1. Sign up for a free account
2. Go to the API Keys section
3. Create a new API key
4. Copy the key (you'll only see it once)

### 2. Configure Environment

Add your OpenRouter key to `.env`:

```bash
OPENROUTER_API_KEY=sk_...your_api_key_here...
```

That's it! No need for separate Claude or OpenAI keys anymore.

### 3. Verify Configuration

Test the connection via the API:

```bash
curl http://localhost:8000/api/ai/test-connection
```

Expected response:
```json
{
  "configured": true,
  "api_key_present": true,
  "base_url": "https://openrouter.ai/api/v1",
  "default_model": "claude-3-sonnet",
  "message": "OpenRouter API is configured"
}
```

## API Endpoints

### Generate Test Steps

**POST** `/api/ai/generate-test-steps`

Generate detailed Playwright test steps from a test description.

**Request:**
```json
{
  "test_description": "User should be able to login with valid credentials",
  "context": "VeriShip Quality Governance Platform"
}
```

**Response:**
```json
{
  "steps": [
    {
      "step_number": 1,
      "action": "navigate",
      "selector": null,
      "expected_result": "Page loaded successfully",
      "description": "Navigate to the application home page"
    },
    {
      "step_number": 2,
      "action": "click",
      "selector": "button[id='login-btn']",
      "expected_result": "Login dialog appears",
      "description": "Click the login button"
    },
    ...
  ],
  "prompt_used": "..."
}
```

**Supported Actions:**
- `navigate` - Go to a URL
- `click` - Click an element
- `type` - Enter text into a field
- `assert` - Verify element exists/state
- `wait` - Wait for element or condition
- `screenshot` - Capture screen
- `hover` - Hover over element
- `select` - Select dropdown option

### Analyze Test Failure

**POST** `/api/ai/analyze-failure`

Get AI-powered suggestions for fixing test failures.

**Parameters:**
- `test_case_title` (string) - Name of the failed test
- `error_message` (string) - Error/exception message
- `steps_executed` (int, optional) - Number of steps that ran before failure

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ai/analyze-failure?test_case_title=Login%20Test&error_message=Element%20not%20found&steps_executed=2"
```

**Response:**
```json
{
  "analysis": "The login button selector may be incorrect...",
  "suggestions": [
    "Check if the button ID changed in the latest build",
    "Try using a more robust selector like button.login-button",
    "Verify the page has fully loaded before clicking"
  ]
}
```

### Test Connection

**GET** `/api/ai/test-connection`

Check OpenRouter API configuration status.

## Available Models

OpenRouter provides access to many models. Switch by adding `?model=MODEL_ID` to requests:

**Popular Models:**
- `claude-3-sonnet` (default) - Fast, balanced, recommended for QA
- `gpt-4` - Most capable, higher cost
- `gpt-3.5-turbo` - Fastest, most economical
- `mistral-medium` - Good balance, lower cost
- `llama-2-70b` - Open source, competitive pricing

**Examples:**

```bash
# Use GPT-4 instead of Claude
curl -X POST http://localhost:8000/api/ai/generate-test-steps \
  -H "Content-Type: application/json" \
  -d '{
    "test_description": "User login",
    "context": "Web app"
  }' \
  -G --data-urlencode "model=gpt-4"
```

## Frontend Integration

### Using AITestGenerator Component

The `src/components/test-runner/AITestGenerator.tsx` component provides a UI for test generation:

```tsx
<AITestGenerator
  onStepsGenerated={(steps) => {
    // Handle generated steps
    console.log('Generated steps:', steps);
  }}
/>
```

**Features:**
- Input test description and context
- Real-time step generation
- Regenerate for alternative suggestions
- Copy steps to clipboard
- Error handling with toasts

### Example Workflow

1. **Describe Test**: "Check that users can create a new project"
2. **Generate Steps**: AI breaks it into click, type, assert steps
3. **Review**: Verify the generated steps make sense
4. **Run**: Execute via Playwright automation
5. **Analyze on Failure**: If it fails, AI suggests fixes

## Cost Estimates

OpenRouter pricing varies by model (checked at generation time):

**Approximate costs per 1000 tests:**
- Claude 3 Sonnet: ~$0.50-$1.00
- GPT-3.5 Turbo: ~$0.10-$0.20
- Mistral Medium: ~$0.25-$0.50

Check [OpenRouter Pricing](https://openrouter.ai/keys) for current rates.

## Common Issues

### "OPENROUTER_API_KEY not set"

**Solution**: Make sure `.env` contains your key:
```bash
OPENROUTER_API_KEY=sk_...
```

Restart the backend after updating `.env`:
```bash
python run.py
```

### "Invalid API Key"

**Solution**: 
- Verify your key starts with `sk_`
- Check it's not expired at openrouter.ai
- Ensure no extra spaces in `.env`

### "Empty or invalid response"

**Solution**:
- Check your OpenRouter account has credits
- Verify internet connection
- Try a different model
- Check error message in backend logs

### Model Not Available

**Solution**:
- Some models have availability windows
- Check [OpenRouter Status](https://openrouter.ai/status)
- Use fallback model like Claude 3 Sonnet

## Best Practices

### 1. Use Descriptive Test Cases

**Good:**
```
"User should be able to login with valid email and password, 
see dashboard, and navigate to Projects page"
```

**Poor:**
```
"Login test"
```

### 2. Provide Context

```json
{
  "test_description": "Admin should be able to disable a user account",
  "context": "VeriShip Quality Governance - Admin panel typically at /admin"
}
```

### 3. Use Appropriate Models

- **Quick Feedback**: Use `gpt-3.5-turbo`
- **Complex Tests**: Use `claude-3-sonnet` or `gpt-4`
- **Cost-Sensitive**: Use `mistral-medium`
- **Open Source Preference**: Use `llama-2-70b`

### 4. Review Generated Steps

AI-generated steps should be reviewed for:
- Correct selectors (may need manual adjustment)
- Realistic browser interactions
- Proper assertion placement
- Correct expected results

### 5. Handle Failures Gracefully

When tests fail:
1. Use `/api/ai/analyze-failure` endpoint
2. Review AI suggestions
3. Fix the underlying issue or selector
4. Re-run test
5. Update test case if needed

## Integration Examples

### With Automation Script

The `automation-runner.js` script can be extended to use AI analysis:

```javascript
async function executeTestWithAIAnalysis(testCaseId) {
  try {
    const result = await executeTestCase(testCaseId);
    if (!result.passed) {
      const analysis = await fetch('/api/ai/analyze-failure', {
        method: 'POST',
        body: JSON.stringify({
          test_case_title: result.testName,
          error_message: result.error,
          steps_executed: result.stepsRun
        })
      });
      console.log('AI Suggestions:', analysis.suggestions);
    }
  } catch (error) {
    console.error(error);
  }
}
```

### With Manual Testing

In the Test Cases page:
1. Generate steps via AITestGenerator
2. Follow the steps manually in the browser
3. Record results via UI
4. If failure, click "Analyze with AI" for suggestions

### With CI/CD Pipeline

Add to GitHub Actions:

```yaml
- name: Run tests with AI analysis
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  run: |
    npm run test:auto
```

## Troubleshooting

### Check Backend Logs

```bash
# Terminal where backend is running
python run.py
```

Look for:
- Authentication errors
- API response errors
- JSON parsing errors

### Test Manually

```bash
# Test API connection
curl http://localhost:8000/api/ai/test-connection

# Generate test steps
curl -X POST http://localhost:8000/api/ai/generate-test-steps \
  -H "Content-Type: application/json" \
  -d '{
    "test_description": "Simple login test",
    "context": "Web application"
  }'

# Analyze failure
curl -X POST "http://localhost:8000/api/ai/analyze-failure?test_case_title=Test&error_message=Failed&steps_executed=1"
```

### Check OpenRouter Account

1. Visit [OpenRouter Dashboard](https://openrouter.ai/account/overview)
2. Verify API key is active
3. Check credit balance
4. Review usage logs for errors

## Next Steps

1. ✅ Set up OpenRouter API key
2. ✅ Test the `/api/ai/test-connection` endpoint
3. Generate your first test steps via the UI or API
4. Review and refine the generated steps
5. Run tests using Playwright automation
6. Use failure analysis for debugging

## Support

- **OpenRouter Docs**: https://openrouter.ai/docs
- **VeriShip Issues**: Check GitHub issues
- **OpenRouter Support**: https://openrouter.ai/support

---

**Last Updated**: 2024
**Model Support**: Claude 3, GPT-4, Llama, Mistral, and more via OpenRouter
