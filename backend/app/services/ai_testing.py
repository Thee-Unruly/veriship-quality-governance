import json
import time
from typing import Optional, List, Dict, Any
import httpx
from pydantic import BaseModel
from app.config import settings

# Models to move things forward
class TestStepRequest(BaseModel):
    test_description: str
    context: str = "Web application testing"


class GeneratedTestStep(BaseModel):
    step_number: int
    action: str  # click, type, navigate, assert, wait, screenshot, etc.
    selector: Optional[str] = None
    expected_result: str
    description: str


class TestStepsResponse(BaseModel):
    steps: List[GeneratedTestStep]
    prompt_used: str


async def call_openrouter_async(user_message: str, model: str = None) -> str:
    """Async helper to call OpenRouter API with error handling and retry logic."""
    if not settings.openrouter_api_key:
        raise ValueError(
            "OpenRouter API key not configured. "
            "Get a key at https://openrouter.ai and add to .env"
        )
    
    max_retries = 3
    retry_delay = 2  # seconds
    target_model = model or settings.openrouter_model
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    f"https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "HTTP-Referer": settings.openrouter_site_url,
                        "X-Title": settings.openrouter_site_name,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": target_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": user_message
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2048,
                    }
                )
                
                # Handle rate limiting with retry
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"[AI] Rate limited (429). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception("OpenRouter API rate limit exceeded after retries.")
                
                if response.status_code != 200:
                    raise Exception(f"OpenRouter API error ({response.status_code}): {response.text}")
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    print(f"[AI] Request failed: {str(e)}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(f"Failed to call OpenRouter API after {max_retries} attempts: {str(e)}")


async def generate_test_steps_openrouter(
    test_description: str,
    context: str = "Web application testing",
    model: str = None
) -> TestStepsResponse:
    """
    Generate test steps using OpenRouter API with robust parsing and error handling.
    """
    prompt = f"""You are an expert QA engineer. Generate detailed Playwright test steps for the following test case:

Test Description: {test_description}
Context: {context}

Generate test steps in JSON format with this exact structure:
[
  {{
    "step_number": 1,
    "action": "navigate",
    "selector": null,
    "expected_result": "Page loaded successfully",
    "description": "Navigate to the application home page"
  }},
  ...
]

Important:
- Actions: navigate, click, type, assert, wait, screenshot, hover, select, etc.
- Include realistic CSS selectors or Playwright locator expressions
- Generate 5-10 steps based on test complexity
- Return ONLY valid JSON array, no markdown, no code blocks, no extra text
- Each step must have all required fields"""

    content = await call_openrouter_async(prompt, model=model)
    
    # Robust JSON extraction
    try:
        json_start = content.find('[')
        json_end = content.rfind(']') + 1
        if json_start != -1 and json_end > json_start:
            json_str = content[json_start:json_end]
            steps_data = json.loads(json_str)
        else:
            steps_data = json.loads(content)
            
        steps = [GeneratedTestStep(**step) for step in steps_data]
        return TestStepsResponse(steps=steps, prompt_used=prompt)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to parse OpenRouter response as JSON: {content[:100]}...\nError: {e}")


def extract_suggestions(text: str) -> List[str]:
    """
    Extract numbered or bulleted suggestions from AI response text
    """
    lines = text.split('\n')
    suggestions = []
    
    for line in lines:
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-') or line.startswith('*')):
            # Remove numbering/bullets/dashes and leading whitespace
            suggestion = line.lstrip('0123456789.-•*) ').strip()
            if suggestion and len(suggestion) > 5:  # Filter out empty/short lines
                suggestions.append(suggestion)
    
    return suggestions[:3]  # Return max 3 suggestions


def check_api_configuration() -> Dict[str, Any]:
    """Check if OpenRouter API is properly configured via settings."""
    return {
        "configured": bool(settings.openrouter_api_key),
        "api_key_present": bool(settings.openrouter_api_key),
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": settings.openrouter_model,
        "message": "OpenRouter API is configured" if settings.openrouter_api_key 
                   else "OPENROUTER_API_KEY environment variable not set",
    }


async def analyze_test_failure(
    test_case_title: str,
    error_message: str,
    steps_executed: int,
    model: str = None,
) -> Dict[str, Any]:
    """
    Use OpenRouter AI to analyze test failures and suggest fixes.
    """
    prompt = f"""A test case failed. Analyze the failure and suggest fixes:

Test Name: {test_case_title}
Steps Executed: {steps_executed}
Error Message: {error_message}

Please provide:
1. Root cause analysis (1-2 sentences) - what likely caused the failure?
2. 2-3 specific actionable suggestions to fix the issue
3. If it looks like a selector issue, suggest possible fixes for the locator

Keep the response concise and practical."""

    try:
        content = await call_openrouter_async(prompt, model=model)
        return {
            "analysis": content,
            "suggestions": extract_suggestions(content),
        }
    except Exception as e:
        return {
            "analysis": f"Error during AI analysis: {str(e)}",
            "suggestions": [],
        }


def extract_suggestions(text: str) -> list[str]:
    """
    Extract numbered or bulleted suggestions from AI response text
    
    Args:
        text: The AI response text to parse
    
    Returns:
        List of up to 3 extracted suggestions
    """
    lines = text.split('\n')
    suggestions = []
    
    for line in lines:
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-') or line.startswith('*')):
            # Remove numbering/bullets/dashes and leading whitespace
            suggestion = line.lstrip('0123456789.-•*) ').strip()
            if suggestion and len(suggestion) > 5:  # Filter out empty/short lines
                suggestions.append(suggestion)
    
    return suggestions[:3]  # Return max 3 suggestions


def check_api_configuration() -> dict:
    """Check if OpenRouter API is properly configured"""
    return {
        "configured": bool(OPENROUTER_API_KEY),
        "api_key_present": bool(OPENROUTER_API_KEY),
        "base_url": OPENROUTER_BASE_URL,
        "default_model": DEFAULT_MODEL,
        "message": "OpenRouter API is configured" if OPENROUTER_API_KEY 
                   else "OPENROUTER_API_KEY environment variable not set",
    }
