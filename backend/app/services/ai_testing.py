"""
AI-powered testing utilities using OpenRouter API
OpenRouter provides access to Claude, GPT-4, Llama, Mistral, and more with a single API key
"""

import os
import json
from typing import Optional
import httpx
from pydantic import BaseModel

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "claude-3-sonnet"  # Can switch to: gpt-4, gpt-3.5-turbo, mistral-medium, llama-2-70b


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
    steps: list[GeneratedTestStep]
    prompt_used: str


async def generate_test_steps_openrouter(
    test_description: str,
    context: str = "Web application testing",
    model: str = DEFAULT_MODEL
) -> TestStepsResponse:
    """
    Generate test steps using OpenRouter API
    
    Supports multiple models:
    - claude-3-sonnet (recommended, fast & cheap)
    - gpt-4
    - gpt-3.5-turbo
    - mistral-medium
    - llama-2-70b
    
    Args:
        test_description: Description of the test case
        context: Additional context about the application
        model: Which model to use (defaults to claude-3-sonnet)
    
    Returns:
        TestStepsResponse with generated steps
    """
    
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY not set. "
            "Get a free key at https://openrouter.ai and add to .env"
        )
    
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
  {{
    "step_number": 2,
    "action": "click",
    "selector": "button[id='login-btn']",
    "expected_result": "Login dialog appears",
    "description": "Click the login button"
  }},
  {{
    "step_number": 3,
    "action": "type",
    "selector": "input[name='username']",
    "expected_result": "Username entered",
    "description": "Enter test username"
  }},
  {{
    "step_number": 4,
    "action": "assert",
    "selector": "div.success-message",
    "expected_result": "Success message visible",
    "description": "Verify success message is displayed"
  }}
]

Important:
- Actions: navigate, click, type, assert, wait, screenshot, hover, select, etc.
- Include realistic CSS selectors or Playwright locator expressions
- Generate 5-10 steps based on test complexity
- Return ONLY valid JSON array, no markdown, no code blocks, no extra text
- Each step must have all required fields"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "VeriShip QA Platform",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2048,
            },
            timeout=60.0
        )
    
    if response.status_code != 200:
        error_details = response.text
        raise Exception(f"OpenRouter API error ({response.status_code}): {error_details}")
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # Parse JSON response
    try:
        steps_data = json.loads(content)
        steps = [GeneratedTestStep(**step) for step in steps_data]
        return TestStepsResponse(steps=steps, prompt_used=prompt)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenRouter response as JSON: {content}\nError: {e}")


async def analyze_test_failure(
    test_case_title: str,
    error_message: str,
    steps_executed: int,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Use OpenRouter AI to analyze test failures and suggest fixes
    
    Args:
        test_case_title: Name of the test that failed
        error_message: Error/exception message from the failure
        steps_executed: Number of steps that ran before failure
        model: Which model to use (defaults to claude-3-sonnet)
    
    Returns:
        Dictionary with analysis and suggestions
    """
    
    if not OPENROUTER_API_KEY:
        return {
            "analysis": "OpenRouter API not configured. Get key at https://openrouter.ai",
            "suggestions": [],
        }
    
    prompt = f"""A test case failed. Analyze the failure and suggest fixes:

Test Name: {test_case_title}
Steps Executed: {steps_executed}
Error Message: {error_message}

Please provide:
1. Root cause analysis (1-2 sentences) - what likely caused the failure?
2. 2-3 specific actionable suggestions to fix the issue
3. If it looks like a selector issue, suggest possible fixes for the locator

Keep the response concise and practical."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "VeriShip QA Platform",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.5,
                "max_tokens": 512,
            },
            timeout=30.0
        )
    
    if response.status_code != 200:
        return {
            "analysis": f"API error occurred: {response.status_code}",
            "suggestions": [],
        }
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    return {
        "analysis": content,
        "suggestions": extract_suggestions(content),
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
