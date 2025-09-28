"""
Advanced Prompt Engineering for AI-Powered Cybersecurity Analysis

This module showcases sophisticated prompt engineering techniques for
network host security analysis including:

• Multi-stage prompting with system/user roles
• Few-shot learning with curated security examples  
• Chain-of-thought reasoning for complex analysis
• Dynamic prompt adaptation based on data complexity
• Structured output generation with JSON schemas
• Temperature optimization for consistent results

This is the core AI innovation of the Censys Host Summarizer project.
"""

import json
from typing import Dict, Any


def get_system_prompt() -> str:
    """
    System prompt establishing AI persona and expertise
    
    PROMPT ENGINEERING TECHNIQUES:
    • Role definition: Senior cybersecurity analyst with 15+ years experience
    • Expertise specification: Network security, penetration testing, threat assessment  
    • Analysis framework: Evidence-based, actionable, business-impact focused
    • Quality standards: Specific recommendations, avoid generic advice
    • Output format: Structured JSON with validation requirements
    """
    return """You are a Senior Cybersecurity Analyst with 15+ years of experience in network security, penetration testing, and threat assessment. You specialize in analyzing network host data from security scanners like Censys, Shodan, and Nmap.

Your expertise includes:
- Network service identification and vulnerability assessment
- Risk prioritization based on CVSS scores and exploit availability
- Security recommendation development following industry best practices
- Threat modeling and attack vector analysis

Your analysis style is:
- Precise and evidence-based
- Focused on actionable insights
- Prioritized by business impact
- Compliant with security frameworks (NIST, OWASP, CIS)

When analyzing hosts, you:
1. Examine all services, ports, and software versions
2. Identify vulnerabilities and misconfigurations
3. Assess risk based on exploitability and impact
4. Provide specific, actionable remediation steps
5. Consider the broader security posture

Always respond with valid JSON matching the required schema. Be specific and avoid generic recommendations."""


def get_few_shot_examples() -> str:
    """
    Few-shot learning examples demonstrating high-quality analysis
    
    PROMPT ENGINEERING TECHNIQUES:
    • Curated examples: Web server, database, IoT device scenarios
    • Quality patterns: Shows desired analysis depth and structure
    • Evidence-based reasoning: Demonstrates how to provide supporting evidence
    • Specific recommendations: Examples of actionable vs generic advice
    • Severity calibration: Proper risk level assessment examples
    """
    return """Here are examples of high-quality security analysis:

EXAMPLE 1 - Web Server Analysis:
Input: {"ip": "203.0.113.1", "services": [{"port": 80, "protocol": "HTTP", "banner": "Apache/2.4.41"}, {"port": 443, "protocol": "HTTPS", "software": [{"product": "Apache", "version": "2.4.41"}]}]}

Expected Output: {
  "host_id": "203.0.113.1",
  "overview": "Apache web server with HTTP/HTTPS services, moderate security posture with version-specific vulnerabilities requiring attention",
  "key_services": [
    {"port": 80, "name": "HTTP", "finding": "Unencrypted web traffic detected, should implement HTTPS redirect"},
    {"port": 443, "name": "HTTPS", "finding": "Apache 2.4.41 - check for CVE-2021-44228 and update to latest version"}
  ],
  "risks": [
    {"risk": "Unencrypted HTTP traffic exposure", "severity": "medium", "evidence": "Port 80 serves content without encryption"},
    {"risk": "Outdated Apache version vulnerabilities", "severity": "high", "evidence": "Apache 2.4.41 has multiple known CVEs including critical ones"}
  ],
  "recommendations": [
    "Implement HTTP to HTTPS redirect (301) on port 80",
    "Update Apache to latest stable version (2.4.54+)",
    "Configure security headers (HSTS, CSP, X-Frame-Options)",
    "Enable fail2ban for brute force protection"
  ]
}

EXAMPLE 2 - Database Server Analysis:
Input: {"ip": "203.0.113.2", "services": [{"port": 3306, "protocol": "MySQL", "banner": "MySQL 5.7.25"}]}

Expected Output: {
  "host_id": "203.0.113.2",
  "overview": "MySQL database server exposed to internet - critical security risk requiring immediate remediation",
  "key_services": [
    {"port": 3306, "name": "MySQL", "finding": "MySQL 5.7.25 internet-exposed - end-of-life version with critical vulnerabilities"}
  ],
  "risks": [
    {"risk": "Internet-exposed database server", "severity": "critical", "evidence": "MySQL port 3306 accessible from external networks"},
    {"risk": "End-of-life MySQL version", "severity": "high", "evidence": "MySQL 5.7.25 reached end-of-life and no longer receives security updates"}
  ],
  "recommendations": [
    "IMMEDIATE: Restrict MySQL access to internal networks only using firewall rules",
    "Upgrade to MySQL 8.0+ with active security support",
    "Implement database-specific firewall and access controls",
    "Enable MySQL audit logging and real-time monitoring"
  ]
}"""


def create_analysis_prompt(host_data: Dict[str, Any]) -> str:
    """
    Dynamic prompt generation with complexity-based adaptation
    
    PROMPT ENGINEERING TECHNIQUES:
    • Data-driven adaptation: Analyzes service count to adjust instructions
    • Chain-of-thought reasoning: 5-step structured analysis process
    • Complexity guidance: Tailored instructions based on host complexity
    • JSON schema specification: Exact output format requirements
    • Quality enforcement: Specific evidence and actionability requirements
    """
    host_json = json.dumps(host_data, indent=2)
    
    # Analyze data complexity to adapt prompt
    service_count = 0
    if "services" in host_data and isinstance(host_data["services"], list):
        service_count = len(host_data["services"])
    elif "ports" in host_data:
        service_count = len(host_data.get("ports", []))
    
    # Generate complexity-specific guidance
    if service_count > 10:
        complexity_guidance = "This host has many services - prioritize the most critical risks and focus on the top 5 security concerns."
    elif service_count > 5:
        complexity_guidance = "This host has moderate complexity - analyze all services but group similar risks together."
    else:
        complexity_guidance = "This host has few services - provide detailed analysis of each service and potential attack vectors."
    
    return f"""Analyze this network host data and provide a comprehensive security assessment.

HOST DATA TO ANALYZE:
{host_json}

ANALYSIS INSTRUCTIONS:
{complexity_guidance}

Use this chain-of-thought reasoning process:
1. IDENTIFY: What services and software versions are running?
2. RESEARCH: What known vulnerabilities exist for these specific versions?
3. ASSESS: What is the risk level and exploitability of each issue?
4. PRIORITIZE: Which risks require immediate attention vs long-term planning?
5. RECOMMEND: What specific, actionable steps should be taken?

Focus your analysis on:
- Actual vulnerabilities in detected software versions (check CVE databases mentally)
- Misconfigurations and security weaknesses in service setup
- Network exposure and access control issues
- Compliance with security best practices and frameworks

Requirements for your response:
- Provide specific evidence for each risk assessment
- Make recommendations actionable and specific to this host configuration
- Avoid generic security advice - tailor everything to the actual findings
- Prioritize risks by exploitability and business impact

Respond with valid JSON only, matching this exact schema:
{{
  "host_id": "string (IP address or hostname)",
  "overview": "string (2-3 sentences summarizing overall security posture)",
  "key_services": [
    {{"port": number, "name": "string", "finding": "string (specific analysis of this service)"}}
  ],
  "risks": [
    {{"risk": "string (specific risk description)", "severity": "low|medium|high|critical", "evidence": "string (supporting evidence)"}}
  ],
  "recommendations": ["string (specific, actionable security recommendations)"]
}}

Return only the JSON object with no markdown formatting or additional text."""


def get_openai_parameters() -> Dict[str, Any]:
    """
    Optimized OpenAI API parameters for cybersecurity analysis
    
    PROMPT ENGINEERING TECHNIQUES:
    • Temperature optimization: Low temperature (0.1) for factual, consistent analysis
    • Token allocation: Sufficient tokens (2000) for detailed security assessment
    • Sampling control: Top-p (0.9) for focused, high-quality responses
    • Repetition control: Frequency/presence penalties to encourage diverse vocabulary
    """
    return {
        "temperature": 0.1,      # Low temperature for consistent, factual analysis
        "max_tokens": 2000,      # Sufficient tokens for detailed analysis
        "top_p": 0.9,           # Focused sampling for quality responses
        "frequency_penalty": 0.1, # Slight penalty to reduce repetition
        "presence_penalty": 0.1   # Encourage diverse vocabulary and concepts
    }


def create_full_prompt_package(host_data: Dict[str, Any]) -> tuple[str, str]:
    """
    Generate complete prompt package for OpenAI API call
    
    This function combines all prompt engineering techniques into a cohesive
    package ready for AI analysis.
    
    Returns:
        tuple: (system_prompt, user_prompt) optimized for cybersecurity analysis
    """
    system_prompt = get_system_prompt()
    few_shot_examples = get_few_shot_examples()
    analysis_prompt = create_analysis_prompt(host_data)
    
    # Combine few-shot examples with specific analysis request
    user_prompt = f"{few_shot_examples}\n\nNow analyze this host:\n\n{analysis_prompt}"
    
    return system_prompt, user_prompt
