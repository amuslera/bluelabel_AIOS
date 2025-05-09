# Bluelabel AIOS - ContentMind

## Project Overview

Bluelabel AIOS (Agentic Intelligence Operating System) is an agent-based AI framework designed to help knowledge workers and creators operate with more clarity, speed, and strategic leverage. The system combines modular AI agents, a structured knowledge repository, and a flexible processing architecture to manage information workflows.

This repository contains the implementation of Bluelabel AIOS's first agent: **ContentMind**, which processes, organizes, and synthesizes multi-format content from articles, PDFs, podcasts, and more - transforming your "read/watch/listen later" backlog into an organized knowledge resource.

## Architecture

### Agent-Based Framework

Bluelabel AIOS is built on a modular agent architecture where:

- Each capability is implemented as a specialized agent
- Agents share common infrastructure and knowledge
- New agents can be added to extend system capabilities
- Agents can collaborate to solve complex tasks

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Bluelabel AIOS Framework Foundation               │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │                 │    │                 │    │                 │  │
│  │   Agent Core    │    │   Knowledge     │    │ Common Services │  │
│  │   Components    │    │   Repository    │    │ (LLM, Processing)│  │
│  │                 │    │                 │    │                 │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                                                     │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
            ┌────────────────────────┬┴───────────────────────┐
            │                        │                        │
            ▼                        ▼                        ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│                     │    │                     │    │                     │
│    ContentMind      │    │    Future Agent     │    │    Future Agent     │
│       Agent         │    │        #2           │    │        #3           │
│                     │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### Core Components

The system consists of these main components:

1. **Agent Framework** - Base classes and interfaces for all agents
2. **Knowledge Repository** - Structured storage for processed information
3. **Model Router** - Intelligent routing between local and cloud LLMs
4. **Processing Pipeline** - Content extraction and analysis workflows
5. **User Interface** - Streamlit-based interface for agent interaction

### Hybrid LLM Architecture

The system uses a hybrid approach to language model processing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Model Router System                        │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Task Analysis & Routing                  │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Complexity  │  │ Location/      │  │ Resource         │  │    │
│  │  │ Assessment  │  │ Availability   │  │ Optimization     │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────┐              ┌─────────────────────────┐  │
│  │                     │              │                         │  │
│  │   Local Models      │◄────────────►│      Cloud APIs         │  │
│  │   (Ollama)          │              │   (OpenAI/Anthropic)    │  │
│  │                     │              │                         │  │
│  └─────────────────────┘              └─────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

- **Local Models** - Ollama-based local inference on Mac Mini
- **Cloud APIs** - OpenAI and Anthropic APIs for complex tasks
- **Intelligent Routing** - Automatic selection based on task requirements
- **Remote Access** - Secure access to local models when away from home

## Initial Agent: ContentMind

The first agent implementation focuses on knowledge management and content processing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ContentMind Agent                            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Content Processing                       │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ URL/Web     │  │ PDF            │  │ Audio            │  │    │
│  │  │ Processing  │  │ Processing     │  │ Processing       │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐                       │    │
│  │  │ Text/HTML   │  │ Social Media   │                       │    │
│  │  │ Processing  │  │ Processing     │                       │    │
│  │  └─────────────┘  └────────────────┘                       │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Knowledge Processing                     │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Summary     │  │ Entity         │  │ Relationship     │  │    │
│  │  │ Generation  │  │ Extraction     │  │ Mapping          │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐                       │    │
│  │  │ Tagging &   │  │ Insight        │                       │    │
│  │  │ Categorizing│  │ Generation     │                       │    │
│  │  └─────────────┘  └────────────────┘                       │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Knowledge Repository                     │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Structured  │  │ Vector         │  │ Content          │  │    │
│  │  │ Metadata    │  │ Embeddings     │  │ Storage          │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Capabilities

- Processes content from URLs, PDFs, text, and audio files
- Extracts key insights, entities, and relationships
- Organizes information with automatic tagging and categorization
- Generates summaries and thematic digests
- Provides search and retrieval across the knowledge base

### Content Types Supported

- Web articles (via URL extraction)
- PDF documents (reports, papers, presentations)
- Plain text and HTML content
- Audio content (podcasts, recorded notes)
- Social media content (threads, posts)

### Use Cases

- Research for writing projects, blog posts, or books
- Exploring new topics and identifying patterns across sources
- Preparing for content creation or speaking engagements
- Tracking developments in areas of interest
- Supporting investment research and decision-making
- Identifying trends and opportunities across disciplines

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Your Home Environment                   │
│                                                             │
│  ┌──────────────┐           ┌──────────────────────────┐    │
│  │              │           │                          │    │
│  │  MacBook Pro │◄─────────►│       Mac Mini M4        │    │
│  │ (Development)│           │   (Local LLM Server)     │    │
│  │              │           │                          │    │
│  └──────────────┘           └──────────────┬───────────┘    │
│                                            │                │
│                                            │                │
└────────────────────────────────────────────┼────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ Secure Gateway   │
                                    │   (Tailscale)    │
                                    └────────┬─────────┘
                                             │
                                             │
┌────────────────────────────────────────────┼────────────────┐
│                                            │                │
│                      Internet              │                │
│                                            │                │
└────────────────────────────────────────────┼────────────────┘
                                             │
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    │            When Remote                  │
                    │    ┌───────────────────────────────┐    │
                    │    │                               │    │
                    │    │   Remote Access to Home LLM   │    │
                    │    │         OR                    │    │
                    │    │   Cloud LLM APIs (Fallback)   │    │
                    │    │                               │    │
                    │    └───────────────────────────────┘    │
                    │                                         │
                    └─────────────────────────────────────────┘
```

## Technical Stack

### Backend
- **Framework**: FastAPI
- **Agent Framework**: LangChain with custom agent architecture
- **Database**: PostgreSQL (production), SQLite (development)
- **Vector Store**: ChromaDB (development), Pinecone (optional for production)
- **Content Processing**: Trafilatura, PyPDF2, Whisper (audio)
- **Task Queue**: Celery with Redis
- **Local LLM**: Ollama (running on Mac Mini M4 Pro)
- **Cloud LLMs**: OpenAI GPT-4, Anthropic Claude

### Frontend
- **Framework**: Streamlit
- **Visualization**: Plotly, Altair
- **Styling**: Streamlit components + custom CSS

### Infrastructure
- **Development**: MacBook Pro
- **Production**: Mac Mini M4 Pro (14-core CPU, 20-core GPU, 48GB RAM)
- **Remote Access**: Tailscale VPN
- **Container Management**: Docker
- **Dependency Management**: Python Virtual Environment

## Development Roadmap

### Phase 1: Foundation (Weeks 1-2)
- Core agent framework implementation
- Knowledge repository structure
- Model router foundation
- Base processing pipeline

### Phase 2: Content Processing (Weeks 3-4)
- URL content extraction
- PDF processing implementation
- Text and HTML processing
- Audio transcription and processing
- Entity and relationship extraction

### Phase 3: Knowledge Organization (Weeks 5-6)
- Vector embeddings implementation
- Automatic tagging and categorization
- Relationship mapping
- Search functionality
- Thematic digest generation

### Phase 4: User Interface (Weeks 7-8)
- Dashboard implementation
- Content browser
- Search interface
- Agent configuration
- Visualization components

### Phase 5: Deployment & Remote Access (Weeks 9-10)
- Mac Mini setup and configuration
- Ollama installation and optimization
- Remote access configuration
- Security implementation
- Performance optimization

## Future Expansion within Bluelabel AIOS

ContentMind serves as the first agent in the "Investor's Second Brain" suite, which will expand to include:

- Market Research Agent
- Pitch Deck Analysis Agent
- Investment Thesis Generator
- Due Diligence Assistant
- Portfolio Monitoring Agent

Additional agent opportunities beyond investment include:

- Content Creation Assistant
- Learning Curriculum Builder
- Trend Analysis Agent
- Expert Network Agent
- Personal Knowledge Graph

## Setup & Usage

### Prerequisites
- Python 3.10+
- Virtual environment (venv, conda, etc.)

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/bluelabel-aios.git
cd bluelabel-aios

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API keys (see .env.example)
```

### Running the Application
```bash
# Start the API server
uvicorn app.main:app --reload

# In a separate terminal, start the Streamlit UI
streamlit run app/ui/streamlit_app.py
```

## Contributing

This is a personal project for now. Contribution guidelines may be added later.

## License

[License information to be determined]