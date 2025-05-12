# Bluelabel AIOS - Extensible Agent Framework

## Project Overview

Bluelabel AIOS (Agentic Intelligence Operating System) is an agent-based AI framework designed to help knowledge workers and creators operate with more clarity, speed, and strategic leverage. The system combines modular AI agents, a structured knowledge repository, and a flexible processing architecture to manage information workflows.

This repository contains the implementation of Bluelabel AIOS's extensible agent framework with two initial agents:

1. **ContentMind**: Processes, organizes, and synthesizes multi-format content from articles, PDFs, podcasts, and more - transforming your "read/watch/listen later" backlog into an organized knowledge resource.

2. **Researcher**: Conducts research on topics and synthesizes information from multiple sources, providing comprehensive answers to research queries.

## Architecture

### Agent-Based Framework

Bluelabel AIOS is built on a modular, extensible agent architecture where:

- Each capability is implemented as a specialized agent
- Agents share common infrastructure and knowledge
- New agents can be easily added to extend system capabilities
- Dynamic agent discovery and configuration through YAML files
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
            ┌────────────────────────┬┴───────────────────────┬────────────────────────┐
            │                        │                        │                        │
            ▼                        ▼                        ▼                        ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│                     │    │                     │    │                     │    │                     │
│    ContentMind      │    │    Researcher       │    │    Gateway          │    │    Future Agents    │
│       Agent         │    │       Agent         │    │       Agent         │    │                     │
│                     │    │                     │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### Core Components

The system consists of these main components:

1. **Agent Framework** - Base classes, interfaces, and registry for all agents
2. **Agent Registry** - Dynamic discovery and management of agent implementations
3. **Knowledge Repository** - Structured storage for processed information
4. **Model Router** - Intelligent routing between local and cloud LLMs
5. **Processing Pipeline** - Content extraction and analysis workflows
6. **Multi-Component Prompting (MCP)** - Framework for reusable prompt templates
7. **Communication Gateways** - Email and messaging integrations for content submission
8. **User Interface** - Streamlit-based interface for agent interaction

### Multi-Component Prompting (MCP) Framework

The MCP framework provides a robust system for creating, managing, and versioning prompt templates:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Multi-Component Prompting Framework              │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │                 │    │                 │    │                 │  │
│  │  Component      │    │   Registry &    │    │  Versioning &   │  │
│  │  Management     │    │   Storage       │    │  History        │  │
│  │                 │    │                 │    │                 │  │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘  │
│           │                      │                      │           │
│           ▼                      ▼                      ▼           │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │                 │    │                 │    │                 │  │
│  │  Template       │    │   Testing &     │    │  API & UI       │  │
│  │  Rendering      │    │   Evaluation    │    │  Integration    │  │
│  │                 │    │                 │    │                 │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                                                     │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
            ┌────────────────────┬─┴───────────────────┐
            │                    │                     │
            ▼                    ▼                     ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│                     │ │                     │ │                     │
│ Agent-Specific      │ │ System Prompts      │ │ Task-Specific       │
│ Components          │ │                     │ │ Components          │
│                     │ │                     │ │                     │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

- **Component Management** - Creation, editing, and organization of prompt components
- **Registry & Storage** - Centralized storage with JSON persistence
- **Versioning & History** - Track changes and compare versions over time
- **Template Rendering** - Variable substitution with required/optional inputs
- **Testing & Evaluation** - Evaluate components with different LLM providers
- **API & UI Integration** - FastAPI endpoints and Streamlit interface

The MCP framework provides substantial benefits:
- **Consistency** - Standard prompts across the application
- **Maintainability** - Central management of prompt templates
- **Versioning** - Track changes and roll back when needed
- **Reusability** - Share components across different agents and tasks
- **Testing** - Evaluate prompt effectiveness with different models

### Communication Gateway Architecture

The system provides multiple channels for content submission through gateway integrations:

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Communication Gateway System                      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                 Content Submission Channels                 │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Email       │  │ WhatsApp       │  │ Streamlit UI     │  │    │
│  │  │ Integration │  │ Integration    │  │ (Direct Upload)  │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                 Content Processing Pipeline                 │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Content     │  │ Type           │  │ Agent            │  │    │
│  │  │ Extraction  │  │ Detection      │  │ Routing          │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────┐              ┌─────────────────────────┐  │
│  │                     │              │                         │  │
│  │  ContentMind        │◄────────────►│     Knowledge           │  │
│  │  Agent              │              │     Repository          │  │
│  │                     │              │                         │  │
│  └─────────────────────┘              └─────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

Each gateway provides:
- Automated content submission without requiring UI interaction
- Content type detection and appropriate processing
- Notification of processing status to users
- Flexible configuration via API endpoints

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

## Implemented Agents

### ContentMind Agent

The ContentMind agent focuses on knowledge management and content processing:

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

### ContentMind Capabilities

- Processes content from URLs, PDFs, text, and audio files
- Extracts key insights, entities, and relationships
- Organizes information with automatic tagging and categorization
- Generates summaries and thematic digests
- Provides search and retrieval across the knowledge base
- Supports automated content submission via email and WhatsApp
- Offers flexible communication gateways for multi-channel input

### Researcher Agent

The Researcher agent focuses on conducting research and synthesizing information:

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Researcher Agent                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                     Research Processing                      │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Query       │  │ Information    │  │ Source           │  │    │
│  │  │ Analysis    │  │ Retrieval      │  │ Evaluation       │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Synthesis Processing                      │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Information │  │ Entity         │  │ Relationship     │  │    │
│  │  │ Integration │  │ Extraction     │  │ Mapping          │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐                       │    │
│  │  │ Insight     │  │ Response       │                       │    │
│  │  │ Generation  │  │ Formatting     │                       │    │
│  │  └─────────────┘  └────────────────┘                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Researcher Capabilities

- Processes research queries and information requests
- Searches for relevant information across multiple sources
- Synthesizes information into comprehensive summaries
- Extracts entities and relationships from research findings
- Organizes results with citations and source attribution
- Provides structured responses with main findings and insights

### Supported Content Types

- **ContentMind Agent**:
  - Web articles (via URL extraction)
  - PDF documents (reports, papers, presentations)
  - Plain text and HTML content
  - Audio content (podcasts, recorded notes)
  - Social media content (threads, posts)

- **Researcher Agent**:
  - Research queries (text-based questions)
  - Text content for analysis and synthesis

### Use Cases

- **ContentMind Agent**:
  - Organizing "read/watch/listen later" content into a knowledge base
  - Preparing for content creation or speaking engagements
  - Tracking developments in areas of interest
  - Supporting investment research and decision-making
  - Identifying trends and opportunities across disciplines

- **Researcher Agent**:
  - Conducting in-depth research on specific topics
  - Answering complex questions with synthesized information
  - Exploring new topics and identifying patterns across sources
  - Supporting decision-making with comprehensive analysis
  - Building knowledge bases on specific domains

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
- **Agent Framework**: Custom agent architecture with modular components
- **Prompt Framework**: Multi-Component Prompting (MCP) with versioning
- **Database**: PostgreSQL (production), SQLite (development)
- **Vector Store**: ChromaDB (development), Pinecone (optional for production)
- **Content Processing**: Trafilatura, PyPDF2, Whisper (audio)
- **Task Queue**: Celery with Redis
- **Local LLM**: Ollama (running on Mac Mini M4 Pro)
- **Cloud LLMs**: OpenAI GPT-4, Anthropic Claude
- **Communication Gateways**: Email (IMAP/SMTP), WhatsApp API

### Frontend
- **Framework**: Streamlit
- **Component UI**: Custom Streamlit-based editor and library for MCP
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

### Phase 5: Multi-Component Prompting (Weeks 9-10)
- Core component system implementation
- Component registry and persistence
- Versioning and history tracking
- Template validation and rendering
- Testing framework integration
- Component editor UI
- Agent integration with components

### Phase 6: Deployment & Remote Access (Weeks 11-12)
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

# Configure and start the email gateway (optional)
# Set up your .env file with email settings first
curl -X POST http://localhost:8080/gateway/email/start

# Configure and start the WhatsApp gateway (optional)
# Set up your .env file with WhatsApp API credentials first
curl -X POST http://localhost:8080/gateway/whatsapp/config -H "Content-Type: application/json" -d '{"phone_id": "your_phone_id", "business_account_id": "your_business_account_id", "api_token": "your_api_token", "verify_token": "your_verify_token", "enabled": true}'
```

## Contributing

This is a personal project for now. Contribution guidelines may be added later.

## License

[License information to be determined]