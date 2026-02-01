# 💼 Wealth Risk Profiling Chatbot

AI-powered client onboarding system for wealth management firms built with FastAPI, Agno, and Ollama.

![API Demo](screenshots/swagger-ui.png)

## 🎯 Features

- ✅ Conversational risk assessment using AI agents
- ✅ Personalized portfolio recommendations
- ✅ Automated PDF report generation
- ✅ Production-ready FastAPI backend
- ✅ Local LLM inference with Ollama (llama3.2)
- ✅ RESTful API with OpenAPI documentation

## 🏗️ Architecture
```
User → FastAPI Backend → Ollama (llama3.2) → Risk Profile + PDF Report
```

## 📊 Demo

### API Documentation
![Swagger UI](screenshots/swagger-ui.png)

### Example Conversation
![Conversation Flow](screenshots/conversation.png)

### Generated PDF Report
![PDF Report](screenshots/pdf-report.png)

## 🚀 Quick Start

### 1. Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup
```bash
git clone <your-repo>
cd wealth-risk-profiler

# Install dependencies
uv sync
```

### 3. Install and Start Ollama
```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from https://ollama.com/download

# Start Ollama server
ollama serve

# Pull the model (in another terminal)
ollama pull llama3.2
```

### 4. Run the API
```bash
# Start development server
uv run uvicorn wealth_risk_profiler.main:app --reload

# API will be available at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### 5. Test the API
```bash
# In another terminal
uv run python tests/test_api.py
```

## 📚 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check (Ollama status) |
| POST | `/api/session/start` | Start new profiling session |
| POST | `/api/chat/{client_id}` | Send message to agent |
| GET | `/api/profile/{client_id}` | Get client profile |
| GET | `/api/report/{client_id}` | Download PDF report |

## 💻 Usage Example
```python
import requests

# Start session
response = requests.post("http://localhost:8000/api/session/start")
data = response.json()
client_id = data["client_id"]
print(data["message"])  # Agent greeting

# Chat with agent
response = requests.post(
    f"http://localhost:8000/api/chat/{client_id}",
    json={"role": "user", "content": "I'm 35 years old"}
)
print(response.json()["message"])  # Agent response

# Download report (when complete)
response = requests.get(f"http://localhost:8000/api/report/{client_id}")
with open("report.pdf", "wb") as f:
    f.write(response.content)
```

## 🐳 Docker Deployment
```bash
# Build and run
docker-compose up --build

# API available at http://localhost:8000
```

## 🧪 Development
```bash
# Add new dependency
uv add <package-name>

# Add dev dependency
uv add --dev pytest

# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

## 📁 Project Structure
```
wealth-risk-profiler/
├── src/
│   └── wealth_risk_profiler/
│       ├── __init__.py
│       ├── main.py              # FastAPI application
│       ├── models.py            # Pydantic models
│       ├── agents/
│       │   ├── __init__.py
│       │   └── risk_profiler.py # Agno agent logic
│       └── utils/
│           ├── __init__.py
│           └── pdf_generator.py # PDF report generation
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── reports/                     # Generated PDF reports
├── pyproject.toml               # Project configuration
├── uv.lock                      # Dependency lock file
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🎨 Tech Stack

- **FastAPI**: Modern web framework for building APIs
- **Agno**: Agentic AI workflow orchestration
- **Ollama**: Local LLM inference (llama3.2)
- **FPDF2**: PDF generation
- **Pydantic**: Data validation
- **UV**: Fast Python package manager

## 🔧 Configuration

The agent can be configured in `src/wealth_risk_profiler/agents/risk_profiler.py`:

- Change LLM model: `create_risk_profiling_agent(model="llama3.2")`
- Adjust prompts and risk scoring logic
- Customize portfolio allocation rules

## 📊 Example Conversation Flow
```
Agent: "Hello! I'm here to help create your personalized investment profile. 
        Let's start - what's your age?"

User: "I'm 28 years old"

Agent: "Great! And what's your investment timeline? How many years are you 
        planning to invest?"

User: "I'm planning for 30 years"

Agent: "Excellent long-term horizon! How would you describe your risk tolerance?
        Are you conservative, moderate, or comfortable with aggressive investments?"

User: "I'm comfortable with high risk for higher returns"

... [continues until profile is complete]

Agent: [Provides JSON with risk score, allocation, insights, next steps]
```

## 🚀 Production Considerations

For production deployment:

1. **Replace in-memory sessions** with Redis/Database
2. **Add authentication** (JWT, OAuth)
3. **Implement rate limiting**
4. **Add logging and monitoring**
5. **Use environment variables** for configuration
6. **Deploy behind HTTPS**
7. **Add input validation and sanitization**

## 📝 License

MIT

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first.

## 👤 Author

**Shriyans Kandhagatla**
- Email: shriyans21k@gmail.com
- LinkedIn: [Your LinkedIn]
- GitHub: [Your GitHub]

---

Built for Product Engineer interview at [Company Name]