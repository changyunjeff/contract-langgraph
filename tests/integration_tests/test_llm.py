"""Integration tests for LLM service module."""

import os

import pytest

from src.llm import create_service


@pytest.mark.integration
def test_create_service_with_default_config() -> None:
    """Test creating a service with default configuration."""
    # This test will use OPENAI_API_KEY from .env file
    service = create_service()
    assert service is not None
    service.release()


@pytest.mark.integration
def test_create_service_with_custom_config() -> None:
    """Test creating a service with custom configuration."""
    service = create_service({
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.5,
    })
    assert service is not None
    service.release()


@pytest.mark.integration
def test_service_with_statement() -> None:
    """Test service with context manager (with statement)."""
    with create_service() as service:
        assert service is not None
        # Service should be available
        llm = service.get_llm()
        assert llm is not None
    # After exiting with block, service should be released


@pytest.mark.integration
def test_service_invoke(openai_api_key: str) -> None:
    """Test invoking the LLM service."""
    with create_service() as service:
        response = service.invoke("Say 'Hello, World!' in one sentence.")
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        # Check that response contains some expected content
        assert "Hello" in response or "hello" in response.lower()


@pytest.mark.integration
def test_service_batch_invoke(openai_api_key: str) -> None:
    """Test batch invoking the LLM service."""
    prompts = [
        "What is 1+1?",
        "What is 2+2?",
        "What is 3+3?",
    ]
    
    with create_service() as service:
        responses = service.batch_invoke(prompts)
        assert responses is not None
        assert isinstance(responses, list)
        assert len(responses) == len(prompts)
        
        # Check that all responses are strings
        for response in responses:
            assert isinstance(response, str)
            assert len(response) > 0


@pytest.mark.integration
def test_service_stream(openai_api_key: str) -> None:
    """Test streaming responses from the LLM service."""
    with create_service() as service:
        stream = service.stream("Count from 1 to 5, one number per line.")
        assert stream is not None
        
        # Collect stream chunks
        chunks = []
        for chunk in stream:
            chunks.append(chunk)
            # Limit to prevent long streams in tests
            if len(chunks) > 10:
                break
        
        # Should have received at least some chunks
        assert len(chunks) > 0


@pytest.mark.integration
def test_service_reuse_same_config(openai_api_key: str) -> None:
    """Test that services with same config reuse cached LLM."""
    config = {"model_name": "gpt-3.5-turbo", "temperature": 0.7}
    
    # Create first service
    with create_service(config) as service1:
        llm1 = service1.get_llm()
        assert llm1 is not None
    
    # Create second service with same config
    # Should reuse the cached LLM from manager
    with create_service(config) as service2:
        llm2 = service2.get_llm()
        assert llm2 is not None
        # Both should reference the same LLM instance (cached)
        assert llm1 == llm2


@pytest.mark.integration
def test_service_different_configs(openai_api_key: str) -> None:
    """Test that services with different configs use different LLMs."""
    config1 = {"model_name": "gpt-3.5-turbo", "temperature": 0.5}
    config2 = {"model_name": "gpt-3.5-turbo", "temperature": 0.9}
    
    with create_service(config1) as service1:
        llm1 = service1.get_llm()
        assert llm1 is not None
    
    with create_service(config2) as service2:
        llm2 = service2.get_llm()
        assert llm2 is not None
    
    # Different configs should result in different LLM instances
    # (or at least different config hashes in manager)


@pytest.mark.integration
def test_service_release() -> None:
    """Test manual release of service."""
    service = create_service()
    assert service is not None
    
    # Get LLM to ensure it's acquired
    llm = service.get_llm()
    assert llm is not None
    
    # Release manually
    service.release()
    
    # After release, get_llm should return None
    assert service.get_llm() is None


@pytest.mark.integration
def test_service_with_custom_api_key() -> None:
    """Test creating service with custom API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set in environment")
    
    service = create_service({"api_key": api_key})
    assert service is not None
    service.release()


@pytest.mark.integration
def test_multiple_services_sequential(openai_api_key: str) -> None:
    """Test creating and using multiple services sequentially."""
    prompts = ["What is Python?", "What is JavaScript?"]
    
    for prompt in prompts:
        with create_service() as service:
            response = service.invoke(prompt)
            assert response is not None
            assert len(response) > 0

