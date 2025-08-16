import os
import re
import requests
import json
import logging
from typing import Dict, List, Optional, Any

# Global variables for API clients
github_session = None
github_headers = {}

def initialize_clients(gemini_api_key: str, github_token: Optional[str] = None):
    """Initialize the GitHub client for repository analysis."""
    global github_session, github_headers
    
    github_session = requests.Session()
    
    # Set up headers for GitHub API
    github_headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'GitHub-Refactoring-Analyzer'
    }
    if github_token:
        github_headers['Authorization'] = f'token {github_token}'

# Supported file extensions for refactoring analysis
REFACTOR_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs', '.java', '.cpp', '.c', '.h',
    '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
    '.html', '.css', '.scss', '.sass', '.less', '.styl', '.vue', '.svelte',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.cfg', '.sql'
}

# Priority files for refactoring analysis
PRIORITY_REFACTOR_FILES = {
    'package.json', 'requirements.txt', 'cargo.toml', 'pom.xml',
    'build.gradle', 'gemfile', 'composer.json', 'setup.py',
    'webpack.config.js', 'vite.config.js', 'rollup.config.js',
    'tsconfig.json', 'babel.config.js', '.eslintrc.js', '.eslintrc.json',
    'dockerfile', 'makefile', 'gruntfile.js', 'gulpfile.js'
}

# Files and directories to skip
SKIP_REFACTOR_PATTERNS = {
    '.git', '.github', '.vscode', '.idea', 'node_modules', '__pycache__',
    'dist', 'build', 'target', 'coverage', '.coverage', '.pytest_cache',
    '.tox', 'venv', 'env', '.env', 'logs', 'tmp', 'temp', '.DS_Store',
    'vendor', 'public/assets', 'static/assets', 'assets/images'
}

# Test file patterns (conditionally included)
TEST_PATTERNS = {
    'test', 'tests', '__tests__', 'spec', 'specs', '.test.', '.spec.',
    '_test.', '_spec.', 'test_', 'spec_'
}

def should_skip_file_for_refactoring(path: str, include_tests: bool = False) -> bool:
    """Check if a file should be skipped for refactoring analysis."""
    path_lower = path.lower()
    
    # Always skip these patterns
    for skip_pattern in SKIP_REFACTOR_PATTERNS:
        if skip_pattern in path_lower:
            return True
    
    # Skip test files if not requested
    if not include_tests:
        for test_pattern in TEST_PATTERNS:
            if test_pattern in path_lower:
                return True
    
    # Skip binary and media files
    if path_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                           '.pdf', '.zip', '.tar', '.gz', '.exe', '.dmg',
                           '.app', '.deb', '.rpm', '.msi', '.woff', '.woff2',
                           '.ttf', '.otf', '.mp3', '.mp4', '.avi', '.mov')):
        return True
    
    return False

def validate_repository(github_url: str) -> Optional[Dict[str, str]]:
    """Validate and extract repository information from GitHub URL."""
    try:
        # Extract owner and repo name from URL
        pattern = r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
        match = re.search(pattern, github_url)
        
        if not match:
            return None
        
        owner, repo_name = match.groups()
        
        # Fetch repository info via GitHub API
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        response = github_session.get(api_url, headers=github_headers)
        
        if response.status_code != 200:
            logging.error(f"GitHub API error: {response.status_code}")
            return None
        
        repo_data = response.json()
        
        return {
            'owner': owner,
            'name': repo_name,
            'full_name': repo_data.get('full_name', f"{owner}/{repo_name}"),
            'description': repo_data.get('description', ''),
            'language': repo_data.get('language', 'Unknown'),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'url': github_url,
            'default_branch': repo_data.get('default_branch', 'main')
        }
        
    except Exception as e:
        logging.error(f"Error validating repository: {e}")
        return None

def get_file_complexity_score(content: str, file_type: str) -> int:
    """Calculate a simple complexity score for a file."""
    score = 0
    lines = content.split('\n')
    
    # Base score on file length
    score += min(len(lines) // 10, 50)  # Max 50 points for length
    
    # Add score for complexity indicators based on file type
    complexity_patterns = {
        'js': ['function', 'class', 'if', 'for', 'while', 'switch', 'try', 'catch'],
        'ts': ['function', 'class', 'interface', 'if', 'for', 'while', 'switch', 'try', 'catch'],
        'py': ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except:', 'lambda'],
        'java': ['public class', 'private', 'protected', 'if', 'for', 'while', 'switch', 'try', 'catch'],
        'cpp': ['class', 'struct', 'if', 'for', 'while', 'switch', 'try', 'catch'],
        'cs': ['class', 'struct', 'interface', 'if', 'for', 'while', 'switch', 'try', 'catch']
    }
    
    ext = file_type.lstrip('.')
    patterns = complexity_patterns.get(ext, ['function', 'class', 'if', 'for', 'while'])
    
    content_lower = content.lower()
    for pattern in patterns:
        score += content_lower.count(pattern.lower()) * 2
    
    return min(score, 100)  # Cap at 100

def fetch_repository_contents_recursive(owner: str, repo_name: str, path: str = "") -> List[Dict]:
    """Recursively fetch repository contents."""
    try:
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"
        response = github_session.get(api_url, headers=github_headers)
        
        if response.status_code != 200:
            logging.warning(f"Could not fetch contents for path {path}: {response.status_code}")
            return []
        
        contents = response.json()
        if not isinstance(contents, list):
            contents = [contents]
        
        all_files = []
        for item in contents:
            if item['type'] == 'file':
                all_files.append(item)
            elif item['type'] == 'dir' and not should_skip_file_for_refactoring(item['path']):
                # Recursively fetch directory contents
                sub_files = fetch_repository_contents_recursive(owner, repo_name, item['path'])
                all_files.extend(sub_files)
        
        return all_files
        
    except Exception as e:
        logging.warning(f"Error fetching contents for path {path}: {e}")
        return []

def fetch_repository_for_refactoring(github_url: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch repository files specifically for refactoring analysis."""
    try:
        # Extract owner and repo name
        pattern = r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
        match = re.search(pattern, github_url)
        if not match:
            raise ValueError("Invalid GitHub URL")
            
        owner, repo_name = match.groups()
        
        # Initialize structure
        structure = {
            'files': [],
            'analyzed_files': {},
            'statistics': {
                'total_files': 0,
                'code_files': 0,
                'analyzed_files': 0,
                'skipped_files': 0,
                'languages': {},
                'complexity_distribution': {}
            }
        }
        
        # Fetch all files recursively
        all_files = fetch_repository_contents_recursive(owner, repo_name)
        
        # Process files
        files_to_analyze = []
        
        for file_info in all_files:
            file_path = file_info['path']
            file_name = file_info['name']
            
            # Skip files based on patterns
            if should_skip_file_for_refactoring(file_path, options.get('include_tests', False)):
                structure['statistics']['skipped_files'] += 1
                continue
            
            # Check if file is relevant for refactoring
            ext = os.path.splitext(file_name)[1].lower()
            is_priority = file_name.lower() in [f.lower() for f in PRIORITY_REFACTOR_FILES]
            is_code_file = ext in REFACTOR_EXTENSIONS
            is_config = options.get('include_config', True) and (is_priority or ext in {'.json', '.yaml', '.yml', '.toml'})
            
            if not (is_code_file or is_config):
                structure['statistics']['skipped_files'] += 1
                continue
            
            file_data = {
                'path': file_path,
                'name': file_name,
                'size': file_info['size'],
                'type': ext,
                'download_url': file_info['download_url'],
                'is_priority': is_priority,
                'complexity_score': 0
            }
            
            structure['files'].append(file_data)
            structure['statistics']['total_files'] += 1
            
            if is_code_file:
                structure['statistics']['code_files'] += 1
                structure['statistics']['languages'][ext] = structure['statistics']['languages'].get(ext, 0) + 1
            
            files_to_analyze.append(file_data)
        
        # Sort files by priority and complexity
        if options.get('focus_large_files', True):
            files_to_analyze.sort(key=lambda x: (not x['is_priority'], -x['size']))
        else:
            files_to_analyze.sort(key=lambda x: (not x['is_priority'], x['size']))
        
        # Limit the number of files to analyze
        max_files = options.get('max_files', 60)  # Increased to support 50 file analysis
        files_to_analyze = files_to_analyze[:max_files]
        
        # Fetch file contents
        for file_data in files_to_analyze:
            try:
                response = github_session.get(file_data['download_url'])
                if response.status_code == 200:
                    content = response.text
                    complexity_score = get_file_complexity_score(content, file_data['type'])
                    
                    structure['analyzed_files'][file_data['path']] = {
                        'content': content,
                        'size': file_data['size'],
                        'type': file_data['type'],
                        'complexity_score': complexity_score,
                        'is_priority': file_data['is_priority']
                    }
                    
                    file_data['complexity_score'] = complexity_score
                    structure['statistics']['analyzed_files'] += 1
                    
                    # Track complexity distribution
                    complexity_range = f"{(complexity_score // 20) * 20}-{(complexity_score // 20) * 20 + 19}"
                    structure['statistics']['complexity_distribution'][complexity_range] = \
                        structure['statistics']['complexity_distribution'].get(complexity_range, 0) + 1
                        
            except Exception as e:
                logging.warning(f"Could not fetch file {file_data['path']}: {e}")
                structure['statistics']['skipped_files'] += 1
        
        return structure
        
    except Exception as e:
        logging.error(f"Error fetching repository for refactoring: {e}")
        raise

def get_language_from_extension(ext: str) -> str:
    """Get programming language from file extension."""
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.sql': 'sql'
    }
    return language_map.get(ext, 'text')

def extract_functions_and_classes(content: str, file_type: str) -> List[Dict[str, str]]:
    """Extract function and class definitions from code."""
    entities = []
    lines = content.split('\n')
    
    # Patterns for different languages
    patterns = {
        '.py': [
            (r'^(\s*)def\s+(\w+)\s*\(', 'function'),
            (r'^(\s*)class\s+(\w+)', 'class'),
            (r'^(\s*)async\s+def\s+(\w+)\s*\(', 'async_function')
        ],
        '.js': [
            (r'^(\s*)function\s+(\w+)\s*\(', 'function'),
            (r'^(\s*)class\s+(\w+)', 'class'),
            (r'^(\s*)async\s+function\s+(\w+)\s*\(', 'async_function'),
            (r'^(\s*)(\w+)\s*:\s*function\s*\(', 'method'),
            (r'^(\s*)(\w+)\s*=>\s*{', 'arrow_function')
        ],
        '.ts': [
            (r'^(\s*)function\s+(\w+)\s*\(', 'function'),
            (r'^(\s*)class\s+(\w+)', 'class'),
            (r'^(\s*)interface\s+(\w+)', 'interface'),
            (r'^(\s*)async\s+function\s+(\w+)\s*\(', 'async_function')
        ],
        '.java': [
            (r'^(\s*)public\s+class\s+(\w+)', 'class'),
            (r'^(\s*)private\s+class\s+(\w+)', 'class'),
            (r'^(\s*)public\s+\w+\s+(\w+)\s*\(', 'method'),
            (r'^(\s*)private\s+\w+\s+(\w+)\s*\(', 'method')
        ]
    }
    
    file_patterns = patterns.get(file_type, [])
    
    for i, line in enumerate(lines):
        for pattern, entity_type in file_patterns:
            match = re.search(pattern, line)
            if match:
                indentation = len(match.group(1)) if match.group(1) else 0
                name = match.group(2)
                entities.append({
                    'name': name,
                    'type': entity_type,
                    'line': i + 1,
                    'indentation': indentation,
                    'content': line.strip()
                })
    
    return entities
