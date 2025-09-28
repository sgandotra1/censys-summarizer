# Censys Host Summarizer

An AI-powered web application that analyzes network host data from Censys and generates security summaries using advanced prompt engineering techniques.

For detailed future enhancements and strategic roadmap, see [FUTURE_ENHANCEMENTS.md](./FUTURE_ENHANCEMENTS.md).

## Features

- **AI-Powered Analysis**: Uses OpenAI GPT with sophisticated prompt engineering
- **Real Data Processing**: Handles actual Censys host data with services and vulnerabilities
- **Modern UI**: Clean, colorful interface for uploading data and viewing results
- **Intelligent Fallback**: Works with or without API key (mock mode for testing)

## Quick Start

### Prerequisites
- Python 3.8+ and Node.js 16+
- OpenAI API key (optional - works in demo mode without)

### Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Optional: Edit .env and add OPENAI_API_KEY=your-key-here
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Access
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Usage

1. **Load Data**: Click "Load sample" or upload your own JSON file
2. **Select Hosts**: Choose hosts to analyze using checkboxes
3. **Analyze**: Click "Summarize X Hosts" to get AI-powered security analysis
4. **Review Results**: View detailed security cards with risks and recommendations
5. **Export**: Click JSON icon to copy analysis data

## Data Format

Supports Censys host data:
```json
{
  "hosts": [
    {
      "ip": "192.168.1.1",
      "services": [
        {
          "port": 22,
          "protocol": "SSH",
          "banner": "SSH-2.0-OpenSSH_8.7",
          "software": [{"product": "OpenSSH", "version": "8.7"}],
          "vulnerabilities": [{"cve": "CVE-2021-41617"}]
        }
      ]
    }
  ]
}
```

## AI Techniques

The application demonstrates advanced prompt engineering:

- **Multi-Stage Prompting**: System role + few-shot examples + specific instructions
- **Few-Shot Learning**: Curated cybersecurity analysis examples for consistent quality
- **Chain-of-Thought**: 5-step reasoning process (Identify → Research → Assess → Prioritize → Recommend)
- **Dynamic Adaptation**: Prompts adjust based on host complexity and service count
- **Temperature Optimization**: Low temperature (0.1) for factual, consistent analysis

All prompt engineering code is in `backend/prompts.py` for easy evaluation.

## Architecture

```
censys-summarizer/
├── backend/
│   ├── app.py              # Main FastAPI application
│   ├── prompts.py          # AI prompt engineering (showcase)
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/                # React application
│   └── package.json        # Node.js dependencies
└── data/
    └── hosts_dataset.json  # Sample Censys data
```

## Technology Stack

**Backend**: FastAPI, OpenAI API, Pydantic
**Frontend**: React 19, Vite, Custom CSS
**AI**: Advanced prompt engineering with GPT-4o-mini

## Testing

### Manual Testing
```bash
# 1. Start both servers (see Quick Start)
# 2. Test basic functionality:
curl http://localhost:8000/health  # Should return {"ok": true, "mode": "AI"}

# 3. Test analysis:
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"hosts":[{"ip":"test","services":[{"port":22,"protocol":"SSH"}]}]}'

# 4. Frontend testing:
# - Visit http://localhost:5173
# - Click "Load sample" → should load 3 hosts
# - Select hosts and click "Summarize" → should show analysis cards
```

### Expected Results
- **AI Mode**: Unique analysis per host with specific recommendations
- **Mock Mode**: Realistic rule-based analysis for demonstration
- **Error Handling**: Clear error messages for invalid data or connection issues

## Development Assumptions

**Technical**: 
- OpenAI API available when key provided
- Modern browser with ES6+ support
- Local development environment

**Data**: 
- JSON input with host/IP identification
- Censys format preferred but handles simple formats
- Service/port information when available

**Operational**: 
- Single-user demo application
- Local development deployment
- Manual file upload workflow

## Troubleshooting

**Backend won't start**: Check Python version (3.8+), activate virtual environment
**Frontend won't start**: Check Node version (16+), run `npm install`
**"Network error"**: Ensure both servers running, check CORS configuration
**AI not working**: Verify API key in .env file, check OpenAI account credits
