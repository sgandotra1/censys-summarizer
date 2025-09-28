"""
Censys Host Summarizer - AI-Powered Security Analysis Backend

A clean, focused implementation of AI-powered network host security analysis
featuring advanced prompt engineering and intelligent fallback systems.

Architecture: 2-file design for optimal clarity
- prompts.py: Advanced prompt engineering techniques (THE SHOWCASE)
- app.py: Main application with models, analysis, and API (THIS FILE)
"""

import json
import os
import asyncio
from typing import List, Dict, Any, Optional, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Import our showcase prompt engineering module
from prompts import create_full_prompt_package, get_openai_parameters

# Load environment variables
load_dotenv()

# Configuration
MODEL = os.getenv("MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")
USE_MOCK = not API_KEY or API_KEY == "your_openai_api_key_here"

# Initialize OpenAI client
openai_client = None
if not USE_MOCK:
    try:
        openai_client = AsyncOpenAI(api_key=API_KEY)
        print(f"🤖 AI MODE: Using OpenAI {MODEL} with advanced prompt engineering")
    except Exception as e:
        USE_MOCK = True
        print(f"⚠️ OpenAI initialization failed: {e}")
        print("🔄 Falling back to mock mode")
else:
    print("🧪 MOCK MODE: AI simulation with sophisticated rule-based analysis")


# ============================================================================
# PYDANTIC MODELS - Data Structure Definitions
# ============================================================================

class KeyService(BaseModel):
    """Network service running on a host"""
    port: Optional[int] = None
    name: Optional[str] = None  
    finding: Optional[str] = None

class Risk(BaseModel):
    """Security risk identified by analysis"""
    risk: str
    severity: Literal["low", "medium", "high", "critical"]
    evidence: Optional[str] = None

class HostSummary(BaseModel):
    """Complete security analysis summary for a single host"""
    host_id: str
    overview: str
    key_services: List[KeyService] = []
    risks: List[Risk] = []
    recommendations: List[str] = []

class SummarizeRequest(BaseModel):
    """API request format for host analysis"""
    hosts: List[Dict[str, Any]] = Field(..., min_items=1)

class SummarizeResponse(BaseModel):
    """API response format containing analysis results"""
    items: List[HostSummary]


# ============================================================================
# ANALYSIS FUNCTIONS - Core Business Logic
# ============================================================================

def extract_host_id(host_data: Dict[str, Any]) -> str:
    """Extract host identifier from host data"""
    return str(host_data.get("ip") or host_data.get("host") or host_data.get("hostname") or "unknown")


def extract_services_and_ports(host_data: Dict[str, Any]) -> tuple[List[int], List[Dict]]:
    """Extract service information from host data"""
    if "services" in host_data and isinstance(host_data["services"], list):
        services_list = host_data["services"]
        ports = [svc.get("port") for svc in services_list if svc.get("port")]
        return ports, services_list
    elif "ports" in host_data:
        ports = host_data.get("ports", [])
        return ports, []
    return [], []


async def ai_analyze_host(host_data: Dict[str, Any]) -> Optional[HostSummary]:
    """
    AI-powered host analysis using advanced prompt engineering
    
    This function demonstrates the complete AI analysis pipeline:
    1. Generate sophisticated prompts using prompts.py
    2. Call OpenAI API with optimized parameters
    3. Parse and validate AI responses
    4. Return structured analysis results
    """
    host_id = extract_host_id(host_data)
    print(f"🤖 AI: Analyzing {host_id} with advanced prompt engineering")
    
    # Generate complete prompt package using our prompt engineering module
    system_prompt, user_prompt = create_full_prompt_package(host_data)
    
    # Get optimized API parameters
    api_params = get_openai_parameters()
    
    # AI Analysis with retry logic
    for attempt in range(3):
        try:
            print(f"🧠 Attempt {attempt + 1}: Calling OpenAI API...")
            
            # Call OpenAI API with advanced prompt engineering
            response = await openai_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                **api_params
            )
            
            # Process AI response
            content = response.choices[0].message.content
            print(f"📝 AI response: {len(content)} characters")
            
            # Clean and parse JSON
            cleaned_content = clean_json_response(content)
            summary_data = json.loads(cleaned_content)
            summary_data["host_id"] = host_id
            
            # Validate and return
            validated_summary = HostSummary(**summary_data)
            print(f"✅ AI analysis successful: {len(validated_summary.risks)} risks, {len(validated_summary.recommendations)} recommendations")
            return validated_summary
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt == 2:  # Last attempt
                print(f"🔄 All AI attempts failed, falling back to mock analysis")
                return mock_analyze_host(host_data)
    
    return None


def mock_analyze_host(host_data: Dict[str, Any]) -> HostSummary:
    """
    Sophisticated mock analysis simulating AI capabilities
    
    This provides realistic security analysis using rule-based logic
    when AI is not available, demonstrating the expected output quality.
    """
    host_id = extract_host_id(host_data)
    ports, services_list = extract_services_and_ports(host_data)
    
    # Generate key services
    key_services = []
    for svc in (services_list or [])[:4]:
        port = svc.get("port")
        protocol = svc.get("protocol", "unknown")
        software = svc.get("software", [])
        
        finding = f"{protocol} service detected"
        if software:
            product = software[0].get("product", "")
            version = software[0].get("version", "")
            if product and version:
                finding = f"{product} {version} - requires security assessment for known CVEs"
        
        key_services.append(KeyService(port=port, name=protocol.upper(), finding=finding))
    
    # Generate security risks based on detected services
    risks = []
    
    # Database exposure check
    if any(p in [3306, 5432, 27017] for p in ports):
        risks.append(Risk(
            risk="Database service exposed to internet",
            severity="critical", 
            evidence="Database ports accessible from external networks"
        ))
    
    # SSH exposure check
    if 22 in ports:
        risks.append(Risk(
            risk="SSH service internet exposure",
            severity="medium",
            evidence="SSH port 22 accessible from external networks"
        ))
    
    # HTTP security check
    if 80 in ports:
        risks.append(Risk(
            risk="Unencrypted HTTP traffic vulnerability",
            severity="medium",
            evidence="HTTP port 80 serves unencrypted content"
        ))
    
    # Check for vulnerabilities in Censys data
    if services_list:
        vuln_count = sum(len(svc.get("vulnerabilities", [])) for svc in services_list)
        if vuln_count > 0:
            severity = "critical" if vuln_count > 5 else "high" if vuln_count > 2 else "medium"
            risks.append(Risk(
                risk="Known security vulnerabilities identified",
                severity=severity,
                evidence=f"{vuln_count} CVE entries found in running services"
            ))
    
    # Default risk if none found
    if not risks:
        risks.append(Risk(
            risk="Network services require security assessment",
            severity="low", 
            evidence="Standard network services detected"
        ))
    
    # Generate targeted recommendations
    recommendations = []
    if any(r.severity == "critical" for r in risks):
        recommendations.append("URGENT: Address critical security risks immediately")
    
    if 22 in ports:
        recommendations.append("Configure SSH key-based authentication and disable password login")
    if 80 in ports:
        recommendations.append("Implement HTTPS with proper SSL/TLS configuration")
    if any(p in [3306, 5432, 27017] for p in ports):
        recommendations.append("Restrict database access to internal networks only")
    
    recommendations.extend([
        "Implement network segmentation and firewall rules",
        "Enable security logging and monitoring",
        "Establish regular vulnerability scanning"
    ])
    
    return HostSummary(
        host_id=host_id,
        overview=f"Network host {host_id} with {len(services_list or ports)} exposed services requiring security assessment",
        key_services=key_services,
        risks=risks,
        recommendations=recommendations[:6]
    )


def clean_json_response(text: str) -> str:
    """Clean up AI response by removing markdown and extracting JSON"""
    text = text.strip()
    
    # Remove markdown code fences
    for fence in ["```json", "```"]:
        if text.startswith(fence):
            text = text[len(fence):]
        if text.endswith("```"):
            text = text[:-3]
    
    # Extract JSON object
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1:
        text = text[start_idx:end_idx + 1]
    
    return text.strip()


async def analyze_single_host(host_data: Dict[str, Any]) -> Optional[HostSummary]:
    """
    Main host analysis function - AI-first with intelligent fallback
    """
    if not USE_MOCK and openai_client:
        return await ai_analyze_host(host_data)
    else:
        await asyncio.sleep(0.5)  # Simulate processing time
        return mock_analyze_host(host_data)


# ============================================================================
# FASTAPI APPLICATION - Web API Layer
# ============================================================================

app = FastAPI(
    title="Censys Host Summarizer",
    description="AI-powered network host security analysis with advanced prompt engineering",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check with AI system information"""
    return {
        "ok": True,
        "mode": "AI" if not USE_MOCK else "Mock",
        "model": MODEL,
        "prompt_engineering": "Advanced multi-stage prompting with few-shot learning",
        "ai_techniques": [
            "Chain-of-thought reasoning",
            "Dynamic prompt adaptation", 
            "Few-shot learning examples",
            "Structured output generation",
            "Temperature optimization"
        ]
    }


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """
    Main analysis endpoint - AI-powered host security analysis
    
    This endpoint demonstrates the complete AI analysis workflow:
    1. Validate incoming host data
    2. Process hosts concurrently using AI or mock analysis
    3. Return structured security analysis results
    """
    if not request.hosts:
        raise HTTPException(status_code=400, detail="No hosts provided")
    
    print(f"📥 Analyzing {len(request.hosts)} hosts using {'AI' if not USE_MOCK else 'Mock'} mode")
    
    # Process all hosts concurrently
    tasks = [analyze_single_host(host) for host in request.hosts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter successful results
    summaries = [r for r in results if isinstance(r, HostSummary)]
    failed = len(results) - len(summaries)
    
    print(f"📤 Analysis complete: {len(summaries)} successful, {failed} failed")
    
    if not USE_MOCK and summaries:
        avg_risks = sum(len(s.risks) for s in summaries) / len(summaries)
        print(f"🎯 AI Quality: {avg_risks:.1f} avg risks per host")
    
    return SummarizeResponse(items=summaries)


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 Censys Host Summarizer - AI Security Analysis")
    print("=" * 60)
    
    if not USE_MOCK:
        print("🤖 AI MODE: Advanced OpenAI Analysis")
        print("🧠 Prompt Engineering: Multi-stage, Few-shot, Chain-of-thought")
        print(f"🔬 Model: {MODEL}")
        print("🎯 Showcased AI Techniques:")
        print("   • System role optimization for cybersecurity expertise")
        print("   • Few-shot learning with curated security examples")
        print("   • Chain-of-thought reasoning for complex analysis")
        print("   • Dynamic prompt adaptation based on data complexity")
        print("   • Structured JSON output with validation")
    else:
        print("🧪 MOCK MODE: Sophisticated AI Simulation")
        print("💡 Add OPENAI_API_KEY to .env for real AI analysis")
    
    print(f"🌐 Server: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
