"""
Setup configuration for Agentic AI Framework.

This allows installation via pip install -e . for development
or pip install . for production use.
"""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() 
        for line in fh 
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="agentic-ai-framework",
    version="0.1.0",
    author="Octaaaaa",
    description="Framework for building multi-agent AI systems with LangGraph orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Octaaaaa/agentic-ai-framework",
    packages=find_packages(exclude=["tests*", "examples*", "docs*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ],
        "openai": ["langchain-openai==0.1.25"],
        "anthropic": ["langchain-anthropic==0.1.23"],
        "google": ["langchain-google-genai==1.0.10"],
    },
    keywords="multi-agent ai langgraph langchain llm agents workflow orchestration",
    project_urls={
        "Bug Reports": "https://github.com/Octaaaaa/agentic-ai-framework/issues",
        "Source": "https://github.com/Octaaaaa/agentic-ai-framework",
        "Documentation": "https://github.com/Octaaaaa/agentic-ai-framework/tree/main/docs",
    },
)
