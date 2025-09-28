"""
Censys Host Summarizer - FastAPI Backend

This backend automatically switches between two modes:
1. MOCK MODE: Rule-based analysis (no API key needed)
2. AI MODE: Real OpenAI GPT analysis (requires valid API key)

To switch to AI mode: Add OPENAI_API_KEY=sk-... to .env file
"""

import json
import os
import asyncio
from typing import List, Dict, Any, Optional, Literal, Tuple
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration - determines if we use real AI or mock analysis
MODEL = os.getenv("MODEL", "gpt-4o-mini")  # OpenAI model to use
API_KEY = os.getenv("OPENAI_API_KEY")       # OpenAI API key (optional)
USE_MOCK = not API_KEY or API_KEY == "your_openai_api_key_here"  # Auto-detect mode

# Pydantic Models - Define the structure of our API data
class KeyService(BaseModel):
    """Represents a network service running on a host"""
    port: Optional[int] = None      # Port number (e.g., 80, 443, 22)
    name: Optional[str] = None      # Service name (e.g., "HTTP", "SSH")
    finding: Optional[str] = None   # Additional details about the service

class Risk(BaseModel):
    """Represents a security risk found on a host"""
    risk: str                                           # Description of the risk
    severity: Literal["low", "medium", "high", "critical"]  # Risk severity level
    evidence: Optional[str] = None                      # Evidence supporting this risk

class HostSummary(BaseModel):
    """Complete security analysis summary for a single host"""
    host_id: str                        # Host identifier (usually IP address)
    overview: str                       # High-level description of the host
    key_services: List[KeyService] = [] # Important services running on the host
    risks: List[Risk] = []              # Security risks identified
    recommendations: List[str] = []     # Security recommendations

class SummarizeRequest(BaseModel):
    """API request format for host analysis"""
    hosts: List[Dict[str, Any]] = Field(..., min_items=1)  # List of host data to analyze

class SummarizeResponse(BaseModel):
    """API response format containing analysis results"""
    items: List[HostSummary]  # List of host analysis summaries

# Initialize FastAPI application
app = FastAPI(title="Censys Host Summarizer", version="1.0.0")

# Configure CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly include OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize OpenAI client (only if we have a valid API key)
openai_client = None
if not USE_MOCK:
    try:
        openai_client = AsyncOpenAI(api_key=API_KEY)
        print(f"✅ AI MODE: Using OpenAI {MODEL} for real analysis")
    except Exception as e:
        USE_MOCK = True
        print(f"⚠️  OpenAI initialization failed: {e}")
        print("🧪 Falling back to mock mode")
else:
    print("🧪 MOCK MODE: Using rule-based analysis (no API key)")


def extract_host_id(host_data: Dict[str, Any]) -> str:
    """
    Extract a unique identifier from host data
    
    Tries common fields in order: ip, host, hostname
    Falls back to "unknown" if none found
    """
    return str(host_data.get("ip") or host_data.get("host") or host_data.get("hostname") or "unknown")


def extract_services_and_ports(host_data: Dict[str, Any]) -> Tuple[List[int], Dict[str, str], List[Dict]]:
    """
    Extract service information from host data, handling different formats
    
    Supports two formats:
    1. Censys format: {"services": [{"port": 80, "protocol": "HTTP"}, ...]}
    2. Simple format: {"ports": [80, 443], "services": {"80": "http", "443": "https"}}
    
    Returns:
        - ports_list: List of port numbers
        - services_dict: Port -> service name mapping
        - services_objects: Full service objects (Censys format only)
    """
    # Handle Censys format: services as array of objects
    if "services" in host_data and isinstance(host_data["services"], list):
        services_list = host_data["services"]
        ports = [svc.get("port") for svc in services_list if svc.get("port")]
        services_dict = {
            str(svc.get("port", "")): svc.get("protocol", "unknown").lower() 
            for svc in services_list if svc.get("port")
        }
        return ports, services_dict, services_list
    
    # Handle simple format: ports array + services dict
    elif "ports" in host_data:
        ports = host_data.get("ports", [])
        services_dict = host_data.get("services", {})
        return ports, services_dict, []
    
    # No service data found
    return [], {}, []


def generate_key_services(ports: List[int], services_dict: Dict[str, str], services_list: List[Dict]) -> List[KeyService]:
    """
    Generate a list of key services from host data
    
    For Censys data: Extracts service details including software versions and banners
    For simple data: Creates basic service entries from port/service mappings
    """
    key_services = []
    
    # For Censys format (rich service data)
    if services_list:
        for svc in services_list[:4]:  # Limit to top 4 services
            port = svc.get("port")
            protocol = svc.get("protocol", "unknown")
            software = svc.get("software", [])
            banner = svc.get("banner", "")
            
            # Generate intelligent finding based on available data
            finding = ""
            if software and len(software) > 0:
                # Extract software product and version
                product = software[0].get("product", "")
                version = software[0].get("version", "")
                finding = f"{product} {version}".strip() if product else protocol
            elif banner:
                # Use service banner (truncated if too long)
                finding = banner[:50] + "..." if len(banner) > 50 else banner
            else:
                # Fallback to basic service detection
                finding = f"{protocol} service detected"
            
            key_services.append(KeyService(
                port=port,
                name=protocol.upper(),
                finding=finding
            ))
    else:
        # For simple format (basic port/service mapping)
        for port in ports[:3]:  # Limit to first 3 ports
            service_name = services_dict.get(str(port), "unknown")
            key_services.append(KeyService(
                port=port,
                name=service_name.upper(),
                finding=f"{service_name} service detected"
            ))
    
    return key_services


def generate_security_risks(ports: List[int], services_list: List[Dict]) -> List[Risk]:
    """
    Generate security risks based on detected services and ports
    
    This is RULE-BASED analysis (not AI) that checks for common security issues:
    - Exposed SSH (port 22)
    - Insecure FTP (port 21) 
    - Unencrypted HTTP (port 80)
    - Exposed databases (ports 3306, 5432, 27017)
    - Known vulnerabilities (from Censys data)
    """
    risks = []
    
    # Define risk detection rules
    risk_checks = [
        # SSH exposure check
        (lambda: 22 in ports or any(svc.get("protocol", "").lower() == "ssh" for svc in services_list),
         Risk(risk="SSH service exposed", severity="medium", evidence="SSH service accessible from internet")),
        
        # FTP security check
        (lambda: 21 in ports or any(svc.get("protocol", "").lower() == "ftp" for svc in services_list),
         Risk(risk="Insecure FTP service", severity="high", evidence="Unencrypted FTP service detected")),
        
        # HTTP encryption check
        (lambda: 80 in ports or any(svc.get("protocol", "").lower() == "http" for svc in services_list),
         Risk(risk="Unencrypted HTTP service", severity="medium", evidence="HTTP traffic not encrypted")),
        
        # Database exposure check
        (lambda: any(str(svc.get("port", "")) in ["3306", "5432", "27017"] for svc in services_list),
         Risk(risk="Database service exposed", severity="critical", evidence="Database port accessible externally"))
    ]
    
    # Apply each risk check
    for check_function, risk_object in risk_checks:
        if check_function():  # If condition is met, add the risk
            risks.append(risk_object)
    
    # Check for actual vulnerabilities in Censys data
    if services_list:
        vuln_count = sum(len(svc.get("vulnerabilities", [])) for svc in services_list)
        if vuln_count > 0:
            risks.append(Risk(
                risk="Known vulnerabilities detected", 
                severity="high", 
                evidence=f"{vuln_count} CVEs found in running services"
            ))
    
    # Default risk if no specific issues found
    if not risks:
        risks.append(Risk(
            risk="Standard network services detected", 
            severity="low", 
            evidence="Common network services are exposed"
        ))
    
    return risks


def generate_recommendations(risks: List[Risk], services_list: List[Dict]) -> List[str]:
    """
    Generate security recommendations
    
    THIS IS WHY RECOMMENDATIONS ARE THE SAME:
    - Uses static templates, not AI reasoning
    - Adds same generic advice to most hosts
    - Only varies based on detected services (SSH, FTP, HTTP)
    """
    recommendations = []
    
    # Priority recommendation for high-risk hosts
    if any(r.severity in ["critical", "high"] for r in risks):
        recommendations.append("Immediate review of critical and high-risk services required")
    
    # Service-specific recommendations (slightly customized)
    if any("SSH" in str(svc.get("protocol", "")).upper() for svc in services_list):
        recommendations.append("Configure SSH key-based authentication and disable password login")
    
    if any("FTP" in str(svc.get("protocol", "")).upper() for svc in services_list):
        recommendations.append("Replace FTP with secure alternatives like SFTP or FTPS")
    
    if any("HTTP" in str(svc.get("protocol", "")).upper() for svc in services_list):
        recommendations.append("Implement HTTPS encryption for all web services")
    
    # THESE ARE ALWAYS THE SAME - Generic security advice added to every host
    generic_recommendations = [
        "Implement network segmentation and firewall rules",
        "Enable regular security updates and vulnerability management",
        "Monitor access logs for suspicious activity"
    ]
    
    recommendations.extend(generic_recommendations)
    return recommendations[:5]  # Limit to 5 total recommendations


def generate_mock_summary(host_data: Dict[str, Any]) -> HostSummary:
    """
    Generate analysis summary using rule-based logic (MOCK MODE)
    
    This function:
    1. Extracts services and ports from the host data
    2. Applies predefined rules to identify risks
    3. Generates template-based recommendations
    4. Returns structured analysis that looks like AI output
    
    NOTE: This is NOT AI - it's pattern matching and templates
    """
    host_id = extract_host_id(host_data)
    ports, services_dict, services_list = extract_services_and_ports(host_data)
    
    # Generate each section using rule-based logic
    key_services = generate_key_services(ports, services_dict, services_list)
    risks = generate_security_risks(ports, services_list)
    recommendations = generate_recommendations(risks, services_list)
    
    return HostSummary(
        host_id=host_id,
        overview=f"Network host {host_id} running {len(services_list or ports)} exposed services",
        key_services=key_services,
        risks=risks,
        recommendations=recommendations
    )


def clean_json_response(text: str) -> str:
    """
    Clean up LLM response text by removing markdown code fences
    
    OpenAI sometimes returns: ```json\n{...}\n```
    This function extracts just the JSON content
    """
    text = text.strip()
    for fence in ["```json", "```"]:
        if text.startswith(fence):
            text = text[len(fence):]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


async def summarize_single_host(host_data: Dict[str, Any]) -> Optional[HostSummary]:
    """
    Analyze a single host - THE MAIN LOGIC SWITCH
    
    This function decides between:
    1. MOCK MODE: Rule-based analysis (current default)
    2. AI MODE: Real OpenAI analysis (if API key provided)
    
    To enable AI mode: Set OPENAI_API_KEY in .env file
    """
    host_id = extract_host_id(host_data)
    
    # MOCK MODE - Rule-based analysis (no AI)
    if USE_MOCK:
        print(f"🧪 MOCK: Analyzing {host_id} with rule-based logic")
        await asyncio.sleep(0.3)  # Simulate API delay for realism
        return generate_mock_summary(host_data)
    
    # AI MODE - Real OpenAI analysis
    print(f"🤖 AI: Sending {host_id} to OpenAI for real analysis")
    
    # Prepare host data for AI analysis
    host_json = json.dumps(host_data, indent=2)
    
    # Create prompt for the AI
    prompt = f"""Analyze this network host and provide a comprehensive security summary.

Host Data:
{host_json}

Please analyze the actual services, vulnerabilities, and configuration details.
Provide specific, actionable insights based on the real data provided.

Respond with valid JSON only:
{{
  "host_id": "{host_id}",
  "overview": "specific description based on actual services and configuration",
  "key_services": [
    {{"port": 80, "name": "HTTP", "finding": "specific findings from the data"}}
  ],
  "risks": [
    {{"risk": "specific risk based on actual findings", "severity": "low|medium|high|critical", "evidence": "specific evidence from the data"}}
  ],
  "recommendations": ["specific, actionable recommendations based on the actual configuration"]
}}

Focus on the actual data provided. Be specific and actionable.
Return only valid JSON, no markdown or extra text."""

    # Try to get AI analysis with retry logic
    for attempt in range(2):  # Original attempt + 1 retry
        try:
            print(f"🤖 Attempt {attempt + 1}: Calling OpenAI API...")
            
            # Call OpenAI API
            response = await openai_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a cybersecurity expert analyzing network hosts. Provide specific, actionable analysis based on the actual data provided. Respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for consistent, factual analysis
                max_tokens=1500   # Enough tokens for detailed analysis
            )
            
            # Extract and clean the AI response
            content = response.choices[0].message.content
            cleaned_content = clean_json_response(content)
            summary_data = json.loads(cleaned_content)
            
            # Ensure host_id is correctly set
            summary_data["host_id"] = host_id
            
            # Validate the response structure
            validated_summary = HostSummary(**summary_data)
            print(f"✅ AI analysis successful for {host_id}")
            return validated_summary
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed on attempt {attempt + 1}: {e}")
            if attempt == 0:  # Retry once on JSON errors
                continue
        except Exception as e:
            print(f"❌ AI analysis failed on attempt {attempt + 1}: {e}")
            if attempt == 0:  # Retry once on any error
                continue
    
    print(f"❌ All attempts failed for {host_id}")
    return None


# API Endpoints

@app.get("/health")
async def health():
    """
    Health check endpoint
    
    Returns {"ok": true} if the service is running
    Used by frontend to verify backend connectivity
    """
    return {"ok": True}


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """
    Main analysis endpoint - processes multiple hosts
    
    This endpoint:
    1. Receives a list of host data objects
    2. Processes each host concurrently (for speed)
    3. Returns analysis summaries for all hosts
    
    Mode switching happens automatically in summarize_single_host()
    """
    if not request.hosts:
        raise HTTPException(status_code=400, detail="No hosts provided")
    
    print(f"📥 Received request to analyze {len(request.hosts)} hosts")
    print(f"🔧 Mode: {'Mock (rule-based)' if USE_MOCK else 'AI (OpenAI)'}")
    
    # Process all hosts concurrently for better performance
    tasks = [summarize_single_host(host) for host in request.hosts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out failed analyses and exceptions
    summaries = []
    failed_count = 0
    
    for i, result in enumerate(results):
        if isinstance(result, HostSummary):
            summaries.append(result)
        else:
            failed_count += 1
            if isinstance(result, Exception):
                print(f"❌ Host {i} failed with exception: {result}")
    
    print(f"📤 Analysis complete: {len(summaries)} successful, {failed_count} failed")
    
    return SummarizeResponse(items=summaries)


# Application entry point
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🚀 Censys Host Summarizer Backend")
    print("=" * 50)
    print(f"📡 Mode: {'🧪 MOCK (rule-based analysis)' if USE_MOCK else '🤖 AI (OpenAI analysis)'}")
    print(f"🔑 API Key: {'❌ Not provided' if USE_MOCK else '✅ Configured'}")
    print(f"🧠 Model: {MODEL}")
    print(f"🌐 Server: http://localhost:8000")
    print("=" * 50)
    
    if USE_MOCK:
        print("💡 To enable AI mode:")
        print("   1. Get an OpenAI API key from https://platform.openai.com/")
        print("   2. Add OPENAI_API_KEY=sk-your-key-here to .env file")
        print("   3. Restart this server")
        print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)