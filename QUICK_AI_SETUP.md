# Next Steps - Get AI Testing Working

## 🎯 Immediate Actions Required

### Step 1: Get Your OpenRouter API Key (5 min)
```bash
1. Visit https://openrouter.ai
2. Create account or sign in
3. Go to API Keys section
4. Create a new key
5. Copy the key (looks like: sk_...)
```

### Step 2: Add API Key to Environment (2 min)
```bash
# Edit backend/.env
OPENROUTER_API_KEY=sk_...paste_your_key_here...
```

### Step 3: Restart Backend (1 min)
```bash
cd backend
python run.py
```

### Step 4: Verify It Works (1 min)
```bash
curl http://localhost:8000/api/ai/test-connection
# Should return: {"configured": true, ...}
```

## ✅ Verification Checklist

- [ ] Got OpenRouter API key from https://openrouter.ai
- [ ] Added `OPENROUTER_API_KEY=sk_...` to `backend/.env`
- [ ] Restarted backend (`python run.py`)
- [ ] Verified connection (`curl http://localhost:8000/api/ai/test-connection`)
- [ ] Got 200 response with `"configured": true`

## 🧪 Test the Features

### Test 1: Generate Test Steps
```bash
curl -X POST http://localhost:8000/api/ai/generate-test-steps \
  -H "Content-Type: application/json" \
  -d '{
    "test_description": "User should be able to login",
    "context": "Web application"
  }'
```

**Expected**: JSON array of test steps with actions, selectors, expected results

### Test 2: Analyze a Failure
```bash
curl -X POST "http://localhost:8000/api/ai/analyze-failure?test_case_title=LoginTest&error_message=Element+not+found&steps_executed=2"
```

**Expected**: Analysis and suggestions for fixing the failure

### Test 3: Use in UI
1. Open VeriShip at http://localhost:3000
2. Go to Test Cases page
3. Use "AI Test Generator" component
4. Describe a test
5. Click "Generate Steps"
6. Review the generated Playwright steps

## 📚 Documentation

Read these for more details:
- [AI_TESTING_GUIDE.md](./AI_TESTING_GUIDE.md) - Complete AI testing guide
- [AUTOMATION_GUIDE.md](./AUTOMATION_GUIDE.md) - How to run tests automatically
- [OPENROUTER_SETUP.md](./OPENROUTER_SETUP.md) - Technical setup details

## 🚀 What You Can Do Now

✅ **Generate Test Steps** - Describe a test, AI creates Playwright steps  
✅ **Analyze Failures** - Feed errors to AI, get fix suggestions  
✅ **Run Automated Tests** - Execute tests via `npm run test:auto`  
✅ **Switch Models** - Use Claude, GPT-4, Mistral, Llama, etc.  
✅ **Cost Effective** - Pay only for what you use  

## ⚡ Example Workflow

1. **Describe**: "User should be able to create a new project with name and description"
2. **Generate**: Click "Generate Steps" → AI creates 8 Playwright steps
3. **Review**: Check selectors and actions are correct
4. **Run**: Execute with `npm run test:auto`
5. **Analyze**: If failure, use AI to suggest fixes
6. **Fix**: Adjust selectors or test logic
7. **Repeat**: Until test passes consistently

## 💡 Pro Tips

- **Best Model for QA**: claude-3-sonnet (fast, cheap, reliable)
- **Most Capable**: gpt-4 (if you need complex reasoning)
- **Most Economical**: gpt-3.5-turbo (good for simple tests)
- **Batch Testing**: Run multiple tests with `npm run test:auto -- [projectId]`
- **CI/CD Ready**: Use `OPENROUTER_API_KEY` environment variable in GitHub Actions

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not set" | Check `backend/.env` has `OPENROUTER_API_KEY=sk_...` |
| "Invalid key" | Verify key starts with `sk_` and isn't expired |
| "Empty response" | Ensure your OpenRouter account has credits |
| "Model unavailable" | Try a different model, Claude 3 Sonnet is most reliable |

## 📞 Help

- OpenRouter: https://openrouter.ai/docs
- Backend logs: `python run.py` terminal
- Check API: `curl http://localhost:8000/api/ai/test-connection`

---

**Once you have your OpenRouter API key, you're ready to go!**  
Estimated time to fully functional: **10 minutes**
