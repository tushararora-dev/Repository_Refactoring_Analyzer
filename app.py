import streamlit as st
import os
import json
import pandas as pd
from typing import Dict, Any, Optional
import github_refactor_analyzer as github_analyzer
import gemini_refactor_engine as refactor_engine
import refactor_report_generator as report_gen

def main():
    st.set_page_config(
        page_title="GitHub Repository Refactoring Analyzer",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 GitHub Repository Refactoring Analyzer")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key configuration
        gemini_api_key = st.text_input(
            "Gemini API Key",
            value=os.getenv("GEMINI_API_KEY"),
            type="password",
            help="Enter your Gemini API key for AI-powered analysis"
        )
        
        github_token = st.text_input(
            "GitHub Token (Optional)",
            value=os.getenv("GITHUB_TOKEN", ""),
            type="password",
            help="GitHub personal access token for higher rate limits"
        )
        
        
        # Analysis Options
        st.subheader("🎯 Analysis Focus")
        analysis_options = {
            'performance': st.checkbox("Performance Optimizations", value=True, help="Analyze loops, algorithms, and API calls"),
            'maintainability': st.checkbox("Code Maintainability", value=True, help="Suggest improvements for readability and structure"),
            'design_patterns': st.checkbox("Design Patterns", value=True, help="Identify better architectural patterns"),
            'code_quality': st.checkbox("Code Quality", value=True, help="Find code smells and best practices"),
            'security': st.checkbox("Security Issues", value=True, help="Identify potential security vulnerabilities"),
            'modularity': st.checkbox("Modularity Improvements", value=True, help="Suggest better separation of concerns")
        }
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📂 Repository Analysis")
        
        # GitHub URL input
        github_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/owner/repository",
            help="Enter the full GitHub repository URL to analyze"
        )
        
        # File type filters
        st.subheader("📁 Analysis Scope")
        col_scope1, col_scope2 = st.columns(2)
        
        with col_scope1:
            max_files = st.slider("Maximum Files to Analyze", 10, 100, 30, help="Limit analysis to most important files")
            include_tests = st.checkbox("Include Test Files", value=False, help="Analyze test files for suggestions")
        
        with col_scope2:
            focus_large_files = st.checkbox("Focus on Large Files", value=True, help="Prioritize larger, more complex files")
            include_config = st.checkbox("Include Config Files", value=True, help="Analyze configuration and build files")
        
        # Analyze button
        if st.button("🔍 Analyze Repository for Refactoring"):
            if not github_url:
                st.error("Please enter a GitHub repository URL")
                return
            
            if not gemini_api_key:
                st.error("Please provide a Gemini API key")
                return
            
            if not any(analysis_options.values()):
                st.error("Please select at least one analysis focus area")
                return
            
            try:
                # Initialize analyzers
                github_analyzer.initialize_clients(gemini_api_key, github_token if github_token else None)
                refactor_engine.initialize_gemini(gemini_api_key)
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Validate repository
                status_text.text("🔍 Validating repository...")
                progress_bar.progress(10)
                
                repo_info = github_analyzer.validate_repository(github_url)
                if not repo_info:
                    st.error("❌ Invalid repository URL or repository not accessible")
                    return
                
                st.success(f"✅ Repository found: **{repo_info['name']}** by {repo_info['owner']}")
                
                # Step 2: Fetch repository structure
                status_text.text("📁 Fetching repository files...")
                progress_bar.progress(30)
                
                scope_options = {
                    'max_files': max_files,
                    'include_tests': include_tests,
                    'focus_large_files': focus_large_files,
                    'include_config': include_config
                }
                
                repo_structure = github_analyzer.fetch_repository_for_refactoring(github_url, scope_options)
                
                # Show repository stats
                stats = repo_structure['statistics']
                st.info(f"📊 Found {stats['total_files']} files, analyzing {stats['analyzed_files']} key files (skipped {stats['skipped_files']} files)")
                
                # Step 3: Generate refactoring suggestions
                status_text.text("🤖 Analyzing code with Gemini 2.5 Pro...")
                progress_bar.progress(60)
                
                refactor_suggestions = refactor_engine.generate_refactor_suggestions(
                    repo_structure, 
                    analysis_options,
                    repo_info
                )
                
                # Step 4: Process and organize suggestions
                status_text.text("📋 Organizing suggestions...")
                progress_bar.progress(90)
                
                # Store results in session state
                st.session_state.refactor_suggestions = refactor_suggestions
                st.session_state.repo_info = repo_info
                st.session_state.analysis_options = analysis_options
                
                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                
                st.success("🎉 Refactoring analysis completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.exception(e)
    
    with col2:

        st.markdown("### 🔍 About This Tool")
        st.markdown("""
        This analyzer examines your GitHub repository and provides:
        - **Performance** optimization suggestions
        - **Maintainability** improvements
        - **Design pattern** recommendations
        - **Code quality** enhancements
        - **Before/after** code examples
        - **Actionable** refactoring steps
        """)

        st.subheader("💡 Quick Examples")        
        example_repos = [
            {
                "name": "Quill Editor",
                "url": "https://github.com/slab/quill",
                "description": "Modern WYSIWYG editor"
            }
        ]

        for repo in example_repos:
            if st.button(f"📁 {repo['name']}", key=repo['url']):
                st.text((f"📄 {repo['url']}"))
    
    # Display results if available
    if hasattr(st.session_state, 'refactor_suggestions') and st.session_state.refactor_suggestions:
        st.markdown("---")
        st.header("📋 Refactoring Suggestions")
        
        # Create tabs for different suggestion categories
        suggestion_tabs = []
        if st.session_state.analysis_options.get('performance'):
            suggestion_tabs.append("🚀 Performance")
        if st.session_state.analysis_options.get('maintainability'):
            suggestion_tabs.append("🔧 Maintainability")
        if st.session_state.analysis_options.get('design_patterns'):
            suggestion_tabs.append("🏗️ Design Patterns")
        if st.session_state.analysis_options.get('code_quality'):
            suggestion_tabs.append("✨ Code Quality")
        if st.session_state.analysis_options.get('security'):
            suggestion_tabs.append("🔒 Security")
        if st.session_state.analysis_options.get('modularity'):
            suggestion_tabs.append("📦 Modularity")
        
        suggestion_tabs.append("📊 Summary")
        suggestion_tabs.append("💾 Export")
        
        tabs = st.tabs(suggestion_tabs)
        suggestions = st.session_state.refactor_suggestions
        
        tab_index = 0
        
        # Performance tab
        if st.session_state.analysis_options.get('performance'):
            with tabs[tab_index]:
                display_performance_suggestions(suggestions.get('performance', {}))
            tab_index += 1
        
        # Maintainability tab
        if st.session_state.analysis_options.get('maintainability'):
            with tabs[tab_index]:
                display_maintainability_suggestions(suggestions.get('maintainability', {}))
            tab_index += 1
        
        # Design Patterns tab
        if st.session_state.analysis_options.get('design_patterns'):
            with tabs[tab_index]:
                display_design_pattern_suggestions(suggestions.get('design_patterns', {}))
            tab_index += 1
        
        # Code Quality tab
        if st.session_state.analysis_options.get('code_quality'):
            with tabs[tab_index]:
                display_code_quality_suggestions(suggestions.get('code_quality', {}))
            tab_index += 1
        
        # Security tab
        if st.session_state.analysis_options.get('security'):
            with tabs[tab_index]:
                display_security_suggestions(suggestions.get('security', {}))
            tab_index += 1
        
        # Modularity tab
        if st.session_state.analysis_options.get('modularity'):
            with tabs[tab_index]:
                display_modularity_suggestions(suggestions.get('modularity', {}))
            tab_index += 1
        
        # Summary tab
        with tabs[tab_index]:
            display_summary_tab(suggestions)
        tab_index += 1
        
        # Export tab
        with tabs[tab_index]:
            display_export_tab()

def display_performance_suggestions(performance_data: Dict[str, Any]):
    """Display performance optimization suggestions."""
    st.subheader("🚀 Performance Optimization Suggestions")
    
    if not performance_data:
        st.info("No performance suggestions found or performance analysis was not selected.")
        return
    
    # Display overall performance score if available
    if 'overall_score' in performance_data:
        col1, col2, col3 = st.columns(3)
        col1.metric("Performance Score", f"{performance_data['overall_score']}/10")
        col2.metric("Issues Found", performance_data.get('issues_count', 0))
        col3.metric("Optimizable Files", performance_data.get('optimizable_files', 0))
    
    # Display specific suggestions
    if 'suggestions' in performance_data:
        for i, suggestion in enumerate(performance_data['suggestions']):
            with st.expander(f"📈 {suggestion.get('title', f'Performance Issue #{i+1}')}"):
                st.markdown(f"**File:** `{suggestion.get('file', 'Unknown')}`")
                st.markdown(f"**Priority:** {suggestion.get('priority', 'Medium')}")
                st.markdown(f"**Impact:** {suggestion.get('impact', 'Unknown')}")
                
                st.markdown("**Issue Description:**")
                st.markdown(suggestion.get('description', 'No description available'))
                
                if 'before_code' in suggestion:
                    st.markdown("**Current Code:**")
                    st.code(suggestion['before_code'], language=suggestion.get('language', 'text'))
                
                if 'after_code' in suggestion:
                    st.markdown("**Optimized Code:**")
                    st.code(suggestion['after_code'], language=suggestion.get('language', 'text'))
                
                if 'explanation' in suggestion:
                    st.markdown("**Why This Helps:**")
                    st.markdown(suggestion['explanation'])

def display_maintainability_suggestions(maintainability_data: Dict[str, Any]):
    """Display maintainability improvement suggestions."""
    st.subheader("🔧 Code Maintainability Improvements")
    
    if not maintainability_data:
        st.info("No maintainability suggestions found or maintainability analysis was not selected.")
        return
    
    # Display maintainability metrics
    if 'metrics' in maintainability_data:
        metrics = maintainability_data['metrics']
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Maintainability Index", metrics.get('maintainability_index', 'N/A'))
        col2.metric("Complex Functions", metrics.get('complex_functions', 0))
        col3.metric("Long Files", metrics.get('long_files', 0))
        col4.metric("Duplicate Code", metrics.get('duplicate_percentage', 'N/A'))
    
    # Display suggestions
    if 'suggestions' in maintainability_data:
        for i, suggestion in enumerate(maintainability_data['suggestions']):
            with st.expander(f"🔧 {suggestion.get('title', f'Maintainability Issue #{i+1}')}"):
                st.markdown(f"**File:** `{suggestion.get('file', 'Unknown')}`")
                st.markdown(f"**Category:** {suggestion.get('category', 'General')}")
                st.markdown(f"**Effort:** {suggestion.get('effort', 'Medium')}")
                
                st.markdown("**Recommendation:**")
                st.markdown(suggestion.get('description', 'No description available'))
                
                if 'current_approach' in suggestion:
                    st.markdown("**Current Approach:**")
                    st.code(suggestion['current_approach'], language=suggestion.get('language', 'text'))
                
                if 'improved_approach' in suggestion:
                    st.markdown("**Improved Approach:**")
                    st.code(suggestion['improved_approach'], language=suggestion.get('language', 'text'))
                
                if 'benefits' in suggestion and isinstance(suggestion['benefits'], list):
                    st.markdown("**Benefits:**")
                    for benefit in suggestion['benefits']:
                        st.markdown(f"- {benefit}")

def display_design_pattern_suggestions(design_patterns_data: Dict[str, Any]):
    """Display design pattern improvement suggestions."""
    st.subheader("🏗️ Design Pattern Recommendations")
    
    if not design_patterns_data:
        st.info("No design pattern suggestions found or design pattern analysis was not selected.")
        return
    
    # Display pattern usage overview
    if 'patterns_found' in design_patterns_data:
        st.markdown("**Existing Patterns Detected:**")
        patterns = design_patterns_data['patterns_found']
        if patterns:
            df = pd.DataFrame(patterns)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No established design patterns detected")
    
    # Display suggestions
    if 'suggestions' in design_patterns_data:
        for i, suggestion in enumerate(design_patterns_data['suggestions']):
            with st.expander(f"🏗️ {suggestion.get('pattern_name', f'Pattern Suggestion #{i+1}')}"):
                st.markdown(f"**Pattern:** {suggestion.get('pattern_name', 'Unknown')}")
                st.markdown(f"**File/Module:** `{suggestion.get('file', 'Unknown')}`")
                st.markdown(f"**Complexity:** {suggestion.get('complexity', 'Medium')}")
                
                st.markdown("**Current Structure:**")
                st.markdown(suggestion.get('current_structure', 'No description available'))
                
                st.markdown("**Recommended Pattern:**")
                st.markdown(suggestion.get('recommended_pattern', 'No recommendation available'))
                
                if 'example_implementation' in suggestion:
                    st.markdown("**Example Implementation:**")
                    st.code(suggestion['example_implementation'], language=suggestion.get('language', 'text'))
                
                if 'benefits' in suggestion and isinstance(suggestion['benefits'], list):
                    st.markdown("**Benefits of This Pattern:**")
                    for benefit in suggestion['benefits']:
                        st.markdown(f"- {benefit}")

def display_code_quality_suggestions(code_quality_data: Dict[str, Any]):
    """Display code quality improvement suggestions."""
    st.subheader("✨ Code Quality Enhancements")
    
    if not code_quality_data:
        st.info("No code quality suggestions found or code quality analysis was not selected.")
        return
    
    # Display quality metrics
    if 'quality_score' in code_quality_data:
        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Quality", f"{code_quality_data['quality_score']}/10")
        col2.metric("Code Smells", code_quality_data.get('code_smells_count', 0))
        col3.metric("Style Issues", code_quality_data.get('style_issues', 0))
    
    # Display suggestions
    if 'suggestions' in code_quality_data:
        for i, suggestion in enumerate(code_quality_data['suggestions']):
            with st.expander(f"✨ {suggestion.get('title', f'Code Quality Issue #{i+1}')}"):
                st.markdown(f"**File:** `{suggestion.get('file', 'Unknown')}`")
                st.markdown(f"**Issue Type:** {suggestion.get('issue_type', 'General')}")
                st.markdown(f"**Severity:** {suggestion.get('severity', 'Medium')}")
                
                st.markdown("**Issue Description:**")
                st.markdown(suggestion.get('description', 'No description available'))
                
                if 'problematic_code' in suggestion:
                    st.markdown("**Problematic Code:**")
                    st.code(suggestion['problematic_code'], language=suggestion.get('language', 'text'))
                
                if 'improved_code' in suggestion:
                    st.markdown("**Improved Code:**")
                    st.code(suggestion['improved_code'], language=suggestion.get('language', 'text'))
                
                if 'explanation' in suggestion:
                    st.markdown("**Why This Matters:**")
                    st.markdown(suggestion['explanation'])

def display_security_suggestions(security_data: Dict[str, Any]):
    """Display security improvement suggestions."""
    st.subheader("🔒 Security Recommendations")
    
    if not security_data:
        st.info("No security suggestions found or security analysis was not selected.")
        return
    
    # Display security overview
    if 'security_score' in security_data:
        col1, col2, col3 = st.columns(3)
        col1.metric("Security Score", f"{security_data['security_score']}/10")
        col2.metric("Vulnerabilities", security_data.get('vulnerabilities_count', 0))
        col3.metric("High Risk Issues", security_data.get('high_risk_issues', 0))
    
    # Display suggestions
    if 'suggestions' in security_data:
        for i, suggestion in enumerate(security_data['suggestions']):
            with st.expander(f"🔒 {suggestion.get('title', f'Security Issue #{i+1}')}"):
                st.markdown(f"**File:** `{suggestion.get('file', 'Unknown')}`")
                st.markdown(f"**Risk Level:** {suggestion.get('risk_level', 'Medium')}")
                st.markdown(f"**Vulnerability Type:** {suggestion.get('vulnerability_type', 'General')}")
                
                st.markdown("**Security Issue:**")
                st.markdown(suggestion.get('description', 'No description available'))
                
                if 'vulnerable_code' in suggestion:
                    st.markdown("**Vulnerable Code:**")
                    st.code(suggestion['vulnerable_code'], language=suggestion.get('language', 'text'))
                
                if 'secure_code' in suggestion:
                    st.markdown("**Secure Code:**")
                    st.code(suggestion['secure_code'], language=suggestion.get('language', 'text'))
                
                if 'mitigation_steps' in suggestion and isinstance(suggestion['mitigation_steps'], list):
                    st.markdown("**Mitigation Steps:**")
                    for step in suggestion['mitigation_steps']:
                        st.markdown(f"- {step}")

def display_modularity_suggestions(modularity_data: Dict[str, Any]):
    """Display modularity improvement suggestions."""
    st.subheader("📦 Modularity Improvements")
    
    if not modularity_data:
        st.info("No modularity suggestions found or modularity analysis was not selected.")
        return
    
    # Display modularity metrics
    if 'cohesion_score' in modularity_data:
        col1, col2, col3 = st.columns(3)
        col1.metric("Cohesion Score", f"{modularity_data['cohesion_score']}/10")
        col2.metric("Coupling Issues", modularity_data.get('coupling_issues', 0))
        col3.metric("Modules Analyzed", modularity_data.get('modules_count', 0))
    
    # Display suggestions
    if 'suggestions' in modularity_data:
        for i, suggestion in enumerate(modularity_data['suggestions']):
            with st.expander(f"📦 {suggestion.get('title', f'Modularity Issue #{i+1}')}"):
                st.markdown(f"**Module/File:** `{suggestion.get('file', 'Unknown')}`")
                st.markdown(f"**Issue Type:** {suggestion.get('issue_type', 'General')}")
                st.markdown(f"**Impact:** {suggestion.get('impact', 'Medium')}")
                
                st.markdown("**Current Structure:**")
                st.markdown(suggestion.get('current_structure', 'No description available'))
                
                st.markdown("**Recommended Refactoring:**")
                st.markdown(suggestion.get('recommended_refactoring', 'No recommendation available'))
                
                if 'example_refactoring' in suggestion:
                    st.markdown("**Example Refactoring:**")
                    st.code(suggestion['example_refactoring'], language=suggestion.get('language', 'text'))
                
                if 'benefits' in suggestion and isinstance(suggestion['benefits'], list):
                    st.markdown("**Benefits:**")
                    for benefit in suggestion['benefits']:
                        st.markdown(f"- {benefit}")

def display_summary_tab(suggestions: Dict[str, Any]):
    """Display summary of all suggestions."""
    st.subheader("📊 Refactoring Summary")
    
    # Count total suggestions across all categories
    total_suggestions = 0
    category_counts = {}
    
    for category, data in suggestions.items():
        if isinstance(data, dict) and 'suggestions' in data:
            count = len(data['suggestions'])
            category_counts[category] = count
            total_suggestions += count
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Suggestions", total_suggestions)
    col2.metric("Categories Analyzed", len(category_counts))
    col3.metric("High Priority", sum(1 for cat_data in suggestions.values() 
                                   if isinstance(cat_data, dict) and cat_data.get('high_priority_count', 0) > 0))
    col4.metric("Quick Wins", sum(1 for cat_data in suggestions.values() 
                                if isinstance(cat_data, dict) and cat_data.get('quick_wins_count', 0) > 0))
    
    # Display category breakdown
    if category_counts:
        st.subheader("Suggestions by Category")
        category_df = pd.DataFrame(list(category_counts.items()), columns=['Category', 'Suggestions'])
        st.bar_chart(category_df.set_index('Category'))
    
    # Display top priority suggestions
    st.subheader("🎯 Top Priority Recommendations")
    
    high_priority_suggestions = []
    for category, data in suggestions.items():
        if isinstance(data, dict) and 'suggestions' in data:
            for suggestion in data['suggestions']:
                if suggestion.get('priority') == 'High' or suggestion.get('severity') == 'High':
                    high_priority_suggestions.append({
                        'Category': category.replace('_', ' ').title(),
                        'Title': suggestion.get('title', 'Untitled'),
                        'File': suggestion.get('file', 'Unknown'),
                        'Impact': suggestion.get('impact', suggestion.get('risk_level', 'Medium'))
                    })
    
    if high_priority_suggestions:
        priority_df = pd.DataFrame(high_priority_suggestions)
        st.dataframe(priority_df, use_container_width=True)
    else:
        st.info("No high-priority issues found. Great job!")

def display_export_tab():
    """Display export options for refactoring suggestions."""
    st.subheader("💾 Export Refactoring Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Generate PDF Report"):
            try:
                pdf_buffer = report_gen.generate_pdf_report(
                    st.session_state.refactor_suggestions,
                    st.session_state.repo_info,
                    st.session_state.analysis_options
                )
                
                st.download_button(
                    label="💾 Download PDF Report",
                    data=pdf_buffer.getvalue(),
                    file_name=f"{st.session_state.repo_info['name']}_refactoring_report.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
    
    with col2:
        if st.button("📊 Generate Excel Report"):
            try:
                excel_buffer = report_gen.generate_excel_report(
                    st.session_state.refactor_suggestions,
                    st.session_state.repo_info
                )
                
                st.download_button(
                    label="💾 Download Excel Report",
                    data=excel_buffer.getvalue(),
                    file_name=f"{st.session_state.repo_info['name']}_refactoring_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"Error generating Excel: {str(e)}")
    
    with col3:
        if st.button("📝 Generate Markdown Report"):
            try:
                markdown_content = report_gen.generate_markdown_report(
                    st.session_state.refactor_suggestions,
                    st.session_state.repo_info,
                    st.session_state.analysis_options
                )
                
                st.download_button(
                    label="💾 Download Markdown",
                    data=markdown_content,
                    file_name=f"{st.session_state.repo_info['name']}_refactoring_suggestions.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"Error generating Markdown: {str(e)}")
    
    # Display JSON export option
    st.markdown("---")
    if st.button("📋 Copy Suggestions as JSON"):
        json_data = json.dumps(st.session_state.refactor_suggestions, indent=2)
        st.text_area("JSON Data (Copy this)", value=json_data, height=200)

if __name__ == "__main__":
    main()
