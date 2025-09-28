# 🛡️ Censys Host Summarizer

A modern web application for AI-powered network host security analysis using real Censys data. Automatically switches between mock analysis (no API key) and real AI analysis (with OpenAI key).

## ✨ Features

- **🤖 Dual Mode**: Mock analysis (rule-based) or real AI analysis (OpenAI GPT)
- **📊 Real Data**: Processes actual Censys host data with services and vulnerabilities  
- **🎨 Modern UI**: Colorful interface with gradients, animations, and responsive design
- **📁 Flexible Input**: Upload JSON files or use sample data
- **📋 Detailed Reports**: Security risks, key services, and actionable recommendations
- **📄 Export**: Copy analysis results as JSON

## 🏗️ Architecture

```
censys-summarizer/
├── .gitignore              # Single root gitignore
├── README.md               # This file
├── backend/
│   ├── .env.example       # Backend environment template
│   ├── requirements.txt   # Python dependencies  
│   └── app.py            # FastAPI server (single file)
├── frontend/
│   ├── .env.example       # Frontend environment template
│   ├── package.json       # Node.js dependencies
│   └── src/               # React application
└── data/
    └── hosts_dataset.json  # Sample Censys data
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ with pip
- Node.js 16+ with npm

### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Start server
python app.py
```

**You'll see:**
```bash
🧪 MOCK MODE: Using rule-based analysis (no API key)
🌐 Server: http://localhost:8000
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create environment file  
cp .env.example .env

# Start development server
npm run dev
```

**Visit:** http://localhost:5173

## 🔑 Environment Configuration

### Backend `.env` (Auto-created from template)
```bash
# Default: Mock mode (no API key needed)
OPENAI_API_KEY=your_openai_api_key_here
MODEL=gpt-4o-mini
```

### Frontend `.env` (Auto-created from template)
```bash
# Points to local backend
VITE_BACKEND_URL=http://localhost:8000
```

## 🤖 Switching to AI Mode

**To enable real AI analysis:**

1. Get OpenAI API key from https://platform.openai.com/
2. Edit `backend/.env`:
   ```bash
   OPENAI_API_KEY=sk-your-real-key-here
   ```
3. Restart backend: `python app.py`
4. You'll see: `🤖 AI MODE: Using OpenAI gpt-4o-mini for real analysis`

## 📖 Usage Guide

1. **Load Data**: Click "Load sample" or "Upload JSON"
2. **Select Hosts**: Use checkboxes to choose hosts for analysis  
3. **Analyze**: Click "Summarize X Hosts" button
4. **Review**: View color-coded security analysis cards
5. **Export**: Click JSON icon to copy analysis data

## 📊 Data Format

Supports Censys host data format:
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

## 🎯 How It Works

### Mock Mode (Default - No API Key)
- **Analysis**: Rule-based pattern matching
- **Risks**: Detected from ports and services (SSH, FTP, HTTP, databases)
- **Recommendations**: Template-based security advice
- **Speed**: Instant results with simulated delay
- **Cost**: Free

### AI Mode (With OpenAI Key)  
- **Analysis**: Real OpenAI GPT reasoning
- **Risks**: AI-identified based on actual configuration
- **Recommendations**: Custom advice per host
- **Speed**: 2-5 seconds per host
- **Cost**: OpenAI API usage

## 🛠️ Technology Stack

**Backend:**
- FastAPI (Python web framework)
- OpenAI API (GPT analysis)
- Pydantic (data validation)
- python-dotenv (environment management)

**Frontend:**
- React 19 (UI framework)
- Vite (build tool)
- Custom CSS (no framework dependencies)

## 🔒 Security & Git

### What's Tracked:
- ✅ Source code and templates
- ✅ Dependencies (`requirements.txt`, `package.json`)
- ✅ Environment templates (`.env.example`)
- ✅ Documentation

### What's Ignored:
- 🔒 Environment files with secrets (`.env`)
- 📦 Dependencies (`node_modules/`, `.venv/`)
- 🏗️ Build artifacts (`dist/`, `__pycache__/`)
- 💻 Editor files (`.vscode/`, `.idea/`)

### Environment Strategy:
1. **Templates committed** (`.env.example`) - Safe, no secrets
2. **Actual files ignored** (`.env`) - May contain API keys
3. **Team onboarding** - Copy template to get started
4. **No accidental commits** - Real secrets auto-ignored

## 🚨 Important Notes

- **API Keys**: Never commit real keys - use templates only
- **Virtual Environment**: Always activate `.venv` before running Python
- **Both Servers**: Backend and frontend must both run
- **Port 8000**: Backend runs on 8000, frontend on 5173
- **Mock Mode**: Works without any API keys for testing

## 🐛 Troubleshooting

**Backend won't start:**
```bash
# Check Python version
python --version  # Should be 3.8+

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Frontend won't start:**
```bash
# Check Node version  
node --version  # Should be 16+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Analysis not working:**
- Check both servers are running
- Verify backend URL in frontend `.env`
- Check browser console for errors
- Ensure `.env` files exist (copy from `.env.example`)

## 📄 License

This project is for educational and demonstration purposes.