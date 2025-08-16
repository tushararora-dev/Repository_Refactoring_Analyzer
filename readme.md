# Overview

This is a GitHub Repository Refactoring Analyzer built with Streamlit that provides AI-powered code analysis and improvement suggestions. The application leverages Gemini 2.5 Pro to analyze any GitHub repository and generate comprehensive refactoring recommendations focused on performance, maintainability, design patterns, code quality, security, and modularity. Users can input a GitHub repository URL, configure analysis options, and receive detailed reports with actionable suggestions for code improvements.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit web application with sidebar configuration and main content areas
- **Layout**: Wide layout with two-column design for repository input and configuration
- **User Interface**: Clean, intuitive interface with checkboxes for analysis options and text inputs for API keys
- **Real-time Interaction**: Streamlit's reactive components for immediate feedback

## Backend Architecture
- **Modular Design**: Separated into distinct modules for different responsibilities:
  - `github_refactor_analyzer.py`: GitHub API integration and repository analysis
  - `gemini_refactor_engine.py`: AI-powered refactoring suggestions using Gemini
  - `refactor_report_generator.py`: Report generation and formatting
- **Analysis Engine**: Multi-faceted analysis system covering performance, maintainability, design patterns, code quality, security, and modularity
- **File Processing**: Intelligent file prioritization analyzing top 50 most important files based on complexity scores and file types
- **Content Filtering**: Smart filtering to exclude non-essential files (tests, build artifacts, dependencies)

## Data Processing
- **Repository Structure Analysis**: Comprehensive codebase statistics including file counts, language distribution, and complexity metrics
- **File Prioritization**: Ranking system based on file importance, complexity, and size
- **Code Analysis**: Support for 20+ programming languages and file formats
- **Content Extraction**: Retrieval and processing of source code from GitHub repositories

## AI Integration
- **Gemini 2.5 Pro**: Primary AI engine for generating refactoring suggestions
- **Prompt Engineering**: Sophisticated prompt construction for targeted analysis based on user preferences
- **Context-Aware Analysis**: Repository-specific analysis considering project type, language, and structure

## Report Generation
- **Markdown Reports**: Comprehensive reports with executive summaries, table of contents, and categorized suggestions
- **Performance Metrics**: Analysis of loops, algorithms, and API call optimizations
- **Design Patterns**: Architectural pattern recommendations and improvements
- **Code Quality**: Best practices and code smell identification

# External Dependencies

## AI Services
- **Google Gemini 2.5 Pro**: Primary AI service for code analysis and refactoring suggestions
- **Authentication**: Requires Gemini API key for AI functionality

## Version Control Integration
- **GitHub API**: Repository access and content retrieval
- **GitHub Personal Access Token**: Optional token for increased rate limits and private repository access
- **REST API**: Standard GitHub v3 API for repository metadata and file content

## Python Libraries
- **Streamlit**: Web application framework for user interface
- **Requests**: HTTP library for GitHub API interactions
- **Pandas**: Data manipulation and analysis
- **Google GenAI**: Official Google library for Gemini API integration

## Development Tools
- **Logging**: Built-in Python logging for debugging and monitoring
- **JSON**: Data serialization for API responses and configuration
- **Regular Expressions**: Pattern matching for file filtering and content analysis
- **Base64**: Encoding for secure handling of GitHub content

## File Format Support
- **Programming Languages**: Python, JavaScript, TypeScript, Java, C/C++, C#, PHP, Ruby, Go, Rust, Swift, Kotlin, Scala
- **JavaScript/TypeScript**: .js, .ts, .jsx, .tsx, .mjs, .cjs (ES modules and CommonJS)
- **Web Technologies**: HTML, CSS, SCSS, SASS, LESS, Stylus, Vue, Svelte
- **Configuration Files**: JSON, XML, YAML, TOML, INI, CFG, SQL
- **Documentation**: Markdown, plain text files
- **Build Systems**: Dockerfile, Makefile, Gradle, Maven configurations