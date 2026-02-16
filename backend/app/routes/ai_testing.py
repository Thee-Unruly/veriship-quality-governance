"""
AI-powered testing endpoints using OpenRouter API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_testing import (
    generate_test_steps_openrouter,
    analyze_test_failure,
    check_api_configuration,
    TestStepRequest,
    TestStepsResponse,
)

router = APIRouter(prefix="/api/ai", tags=["AI Testing"])

@router.post("/generate-test-steps", response_model=TestStepsResponse)
async def generate_test_steps(request: TestStepRequest):
    """
    Generate test steps using OpenRouter AI
    
    Supports multiple models via OpenRouter:
    - claude-3-sonnet (default, recommended)
    - gpt-4
    - gpt-3.5-turbo
    - mistral-medium
    - llama-2-70b
    
    Example request:
    {
      "test_description": "User should be able to login with valid credentials",
      "context": "VeriShip Quality Governance Platform"
    }
    """
    try:
        result = await generate_test_steps_openrouter(
            request.test_description,
            request.context
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate test steps: {str(e)}"
        )

@router.post("/analyze-failure")
async def analyze_failure(
    test_case_title: str,
    error_message: str,
    steps_executed: int = 0
):
    """
    Analyze a test failure and get AI suggestions for fixes
    
    Uses OpenRouter to provide intelligent failure analysis
    
    Example:
    POST /api/ai/analyze-failure?test_case_title=Login%20Test&error_message=Element%20not%20found&steps_executed=2
    """
    try:
        analysis = await analyze_test_failure(
            test_case_title,
            error_message,
            steps_executed
        )
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze failure: {str(e)}"
        )

@router.get("/test-connection")
async def test_ai_connection():
    """Test if OpenRouter API is configured"""
    config = check_api_configuration()
    return {
        "configured": config["configured"],
        "api_key_present": config["api_key_present"],
        "base_url": config["base_url"],
        "default_model": config["default_model"],
        "message": config["message"]
    }
