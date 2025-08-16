import os
import json
import logging
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types

# Global Gemini client
gemini_client = None

def initialize_gemini(api_key: str):
    """Initialize the Gemini client."""
    global gemini_client
    gemini_client = genai.Client(api_key=api_key)

def build_refactoring_prompt(repo_structure: Dict, analysis_options: Dict, repo_info: Dict) -> str:
    """Build a comprehensive prompt for refactoring analysis."""
    
    # Repository overview
    stats = repo_structure['statistics']
    overview = f"""## Repository Analysis for Refactoring

**Repository:** {repo_info['full_name']}
**Main Language:** {repo_info['language']}
**Description:** {repo_info['description']}

**Codebase Statistics:**
- Total files analyzed: {stats['analyzed_files']}
- Code files: {stats['code_files']}
- Primary languages: {', '.join(stats['languages'].keys())}
- Complexity distribution: {stats.get('complexity_distribution', {})}

"""
    
    # Add file contents with priority ordering
    files_content = "## Source Code Files for Analysis:\n\n"
    
    # Sort files by priority and complexity
    sorted_files = sorted(
        repo_structure['analyzed_files'].items(),
        key=lambda x: (not x[1]['is_priority'], -x[1]['complexity_score'], -x[1]['size'])
    )
    
    # Include top files for analysis
    for file_path, file_data in sorted_files[:50]:  # Analyze top 50 files
        files_content += f"### File: `{file_path}`\n"
        files_content += f"- **Type:** {file_data['type']}\n"
        files_content += f"- **Size:** {file_data['size']} bytes\n"
        files_content += f"- **Complexity Score:** {file_data['complexity_score']}/100\n"
        files_content += f"- **Priority File:** {'Yes' if file_data['is_priority'] else 'No'}\n\n"
        
        # Include file content (truncate if too long)
        content = file_data['content']
        if len(content) > 20000:  # Truncate very long files
            content = content[:10000] + "\n\n... [File truncated for analysis] ...\n\n" + content[-10000:]
        
        files_content += f"```{file_data['type'].lstrip('.')}\n{content}\n```\n\n"
    
    # Build analysis focus areas
    focus_areas = []
    if analysis_options.get('performance'):
        focus_areas.append("**Performance Optimizations:** Identify slow algorithms, inefficient loops, unnecessary API calls, memory leaks, and optimization opportunities")
    if analysis_options.get('maintainability'):
        focus_areas.append("**Code Maintainability:** Find complex functions, improve naming, reduce code duplication, enhance readability")
    if analysis_options.get('design_patterns'):
        focus_areas.append("**Design Patterns:** Suggest better architectural patterns, SOLID principles, separation of concerns")
    if analysis_options.get('code_quality'):
        focus_areas.append("**Code Quality:** Identify code smells, improve error handling, enhance documentation")
    if analysis_options.get('security'):
        focus_areas.append("**Security Issues:** Find vulnerabilities like SQL injection, XSS, insecure authentication, data exposure")
    if analysis_options.get('modularity'):
        focus_areas.append("**Modularity:** Improve separation of concerns, reduce coupling, increase cohesion")
    
    # Build the main prompt
    main_prompt = f"""{overview}

{files_content}

## Refactoring Analysis Request

As a senior software architect and code review expert, analyze the provided codebase and generate specific, actionable refactoring suggestions focusing on:

{chr(10).join(focus_areas)}

## Required Output Format (JSON):

Provide your analysis in the following JSON structure:

"""
    
    # Add JSON structure based on selected options
    json_structure = "{\n"
    
    if analysis_options.get('performance'):
        json_structure += '''  "performance": {
    "overall_score": 0-10,
    "issues_count": number,
    "optimizable_files": number,
    "suggestions": [
      {
        "title": "Specific performance issue title",
        "file": "path/to/file.ext",
        "priority": "High|Medium|Low",
        "impact": "Description of performance impact",
        "description": "Detailed description of the issue",
        "before_code": "Current inefficient code",
        "after_code": "Optimized code example",
        "explanation": "Why this optimization helps",
        "language": "programming_language"
      }
    ]
  },
'''
    
    if analysis_options.get('maintainability'):
        json_structure += '''  "maintainability": {
    "metrics": {
      "maintainability_index": "score",
      "complex_functions": number,
      "long_files": number,
      "duplicate_percentage": "percentage"
    },
    "suggestions": [
      {
        "title": "Maintainability improvement title",
        "file": "path/to/file.ext",
        "category": "Complexity|Duplication|Naming|Structure",
        "effort": "Low|Medium|High",
        "description": "What needs to be improved",
        "current_approach": "Current problematic code",
        "improved_approach": "Better structured code",
        "benefits": ["benefit1", "benefit2"],
        "language": "programming_language"
      }
    ]
  },
'''
    
    if analysis_options.get('design_patterns'):
        json_structure += '''  "design_patterns": {
    "patterns_found": [
      {
        "pattern": "Pattern name",
        "file": "path/to/file.ext",
        "quality": "Good|Poor|Missing"
      }
    ],
    "suggestions": [
      {
        "pattern_name": "Recommended pattern name",
        "file": "path/to/file.ext",
        "complexity": "Low|Medium|High",
        "current_structure": "Description of current approach",
        "recommended_pattern": "Why this pattern would help",
        "example_implementation": "Code example of pattern implementation",
        "benefits": ["benefit1", "benefit2"],
        "language": "programming_language"
      }
    ]
  },
'''
    
    if analysis_options.get('code_quality'):
        json_structure += '''  "code_quality": {
    "quality_score": 0-10,
    "code_smells_count": number,
    "style_issues": number,
    "suggestions": [
      {
        "title": "Code quality issue title",
        "file": "path/to/file.ext",
        "issue_type": "Code Smell|Style|Error Handling|Documentation",
        "severity": "High|Medium|Low",
        "description": "Description of the quality issue",
        "problematic_code": "Current problematic code",
        "improved_code": "Better quality code",
        "explanation": "Why this improvement matters",
        "language": "programming_language"
      }
    ]
  },
'''
    
    if analysis_options.get('security'):
        json_structure += '''  "security": {
    "security_score": 0-10,
    "vulnerabilities_count": number,
    "high_risk_issues": number,
    "suggestions": [
      {
        "title": "Security vulnerability title",
        "file": "path/to/file.ext",
        "risk_level": "Critical|High|Medium|Low",
        "vulnerability_type": "SQL Injection|XSS|Authentication|Data Exposure|etc",
        "description": "Description of the security issue",
        "vulnerable_code": "Current vulnerable code",
        "secure_code": "Secure implementation",
        "mitigation_steps": ["step1", "step2"],
        "language": "programming_language"
      }
    ]
  },
'''
    
    if analysis_options.get('modularity'):
        json_structure += '''  "modularity": {
    "cohesion_score": 0-10,
    "coupling_issues": number,
    "modules_count": number,
    "suggestions": [
      {
        "title": "Modularity improvement title",
        "file": "path/to/file.ext",
        "issue_type": "High Coupling|Low Cohesion|Responsibility Mixing",
        "impact": "High|Medium|Low",
        "current_structure": "Description of current module structure",
        "recommended_refactoring": "How to improve modularity",
        "example_refactoring": "Code example of better structure",
        "benefits": ["benefit1", "benefit2"],
        "language": "programming_language"
      }
    ]
  },
'''
    
    # Remove trailing comma and close JSON
    json_structure = json_structure.rstrip(',\n')
    json_structure += "\n}"
    
    # Complete the prompt
    complete_prompt = main_prompt + json_structure + """

## Important Instructions:
- Focus ONLY on the specific analysis areas selected
- Provide concrete, actionable suggestions with code examples
- Include specific file paths and line numbers when possible
- Prioritize high-impact improvements
- Ensure all JSON is properly formatted and complete
- Be specific and technical in your recommendations

Generate your refactoring analysis now.
"""
    
    return complete_prompt

def generate_refactor_suggestions(repo_structure: Dict, analysis_options: Dict, repo_info: Dict) -> Dict[str, Any]:
    """Generate refactoring suggestions using Gemini."""
    try:
        # Build the analysis prompt
        prompt = build_refactoring_prompt(repo_structure, analysis_options, repo_info)
        
        # Generate suggestions with Gemini
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
                max_output_tokens=100000
            )
        )
        
        if response.text:
            try:
                # Parse the JSON response
                suggestions = json.loads(response.text)
                return suggestions
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse Gemini response as JSON: {e}")
                # Return a fallback structure
                return {
                    "error": "Failed to parse AI response",
                    "raw_response": response.text[:1000] + "..." if len(response.text) > 1000 else response.text
                }
        else:
            logging.error("Empty response from Gemini")
            return {"error": "Empty response from AI service"}
            
    except Exception as e:
        logging.error(f"Error generating refactor suggestions: {e}")
        return {
            "error": f"Failed to generate suggestions: {str(e)}",
            "suggestions": []
        }