.PHONY: test test-local lint clean

# Run all tests with mocked LLM — no live model or network required
test-local:
	MOCK_LLM=true pytest tests/ -v

# CI target — identical to test-local; used by .github/workflows/ci.yml
test:
	MOCK_LLM=true pytest tests/ -v

lint:
	flake8 src/ tests/ --max-line-length=100 --ignore=E501,W503

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; \
	echo "Clean done"
