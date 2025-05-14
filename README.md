# Bluelabel AIOS - Extensible Agent Framework

## Project Overview

Bluelabel AIOS (Agentic Intelligence Operating System) is an agent-based AI framework designed to help knowledge workers and creators operate with more clarity, speed, and strategic leverage. The system combines modular AI agents, a structured knowledge repository, and a flexible processing architecture to manage information workflows.

This repository contains the implementation of Bluelabel AIOS's extensible agent framework with the following agents:

1. **ContentMind**: Processes, organizes, and synthesizes multi-format content from articles, PDFs, podcasts, and more - transforming your "read/watch/listen later" backlog into an organized knowledge resource.

2. **Researcher**: Conducts research on topics and synthesizes information from multiple sources, providing comprehensive answers to research queries.

3. **Gateway**: Handles incoming content from various channels such as email and WhatsApp, automatically processing and routing to appropriate agents.

4. **Digest**: Generates daily or on-demand summaries of content, identifies themes and connections, and delivers insights via email or messaging platforms.

## Recent Updates

- Fixed Gateway agent email processing and routing to Researcher agent for research queries
- Researcher agent now always provides a model parameter to LLM (fixes OpenAI API errors)
- Improved debug logging in Gateway and Researcher agents for easier troubleshooting
- End-to-end test: Gateway email simulation now correctly triggers research workflow and LLM call

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

### Gateway Agent

The Gateway agent handles content intake from communication channels:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Gateway Agent                               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Channel Processing                       │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Email       │  │ WhatsApp       │  │ Other Messaging  │  │    │
│  │  │ Processing  │  │ Processing     │  │ Platforms        │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Content Classification                   │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Type        │  │ Priority       │  │ Agent            │  │    │
│  │  │ Detection   │  │ Assessment     │  │ Routing          │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    User Management                          │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Preference  │  │ Notification   │  │ Interaction      │  │    │
│  │  │ Management  │  │ Management     │  │ History          │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Gateway Agent Capabilities

- Monitors email and messaging channels for new content
- Extracts content from various formats (links, attachments, text)
- Classifies content and determines appropriate processing agent
- Routes content to ContentMind, Researcher, or other agents
- Maintains processing history and user preferences
- Sends status notifications back to the user
- Handles authentication and security for communication channels
- Processes commands and requests in natural language

### Digest Agent

The Digest agent creates summaries and identifies connections across content in the knowledge repository:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Digest Agent                                │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Content Analysis                          │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Theme       │  │ Connection     │  │ Cross-Reference  │  │    │
│  │  │ Identification │ Discovery      │  │ Analysis         │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Digest Generation                        │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Content     │  │ Insight        │  │ Formatting       │  │    │
│  │  │ Aggregation │  │ Extraction     │  │ Templates        │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └────────────────────────────┬────────────────────────────────┘    │
│                               │                                     │
│                               ▼                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Delivery & Scheduling                    │    │
│  │                                                             │    │
│  │  ┌─────────────┐  ┌────────────────┐  ┌──────────────────┐  │    │
│  │  │ Email       │  │ Messaging      │  │ Scheduled        │  │    │
│  │  │ Delivery    │  │ Delivery       │  │ Distribution     │  │    │
│  │  └─────────────┘  └────────────────┘  └──────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Digest Agent Capabilities

- Aggregates content from the knowledge repository based on time period or tags
- Identifies common themes across content items
- Discovers connections between different pieces of content
- Extracts insights and identifies patterns
- Formats digests for different delivery channels
- Supports scheduled delivery (daily, weekly, monthly)
- Delivers digests via email or messaging platforms
- Allows on-demand digest generation with custom parameters
- Stores digest history for later reference

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

- **Gateway Agent**:
  - Email messages with attachments or links
  - WhatsApp messages and media
  - Command processing via messaging platforms
  - Natural language content submission

- **Digest Agent**:
  - Content from knowledge repository
  - Time-based content selection (daily, weekly, monthly)
  - Tag-based content filtering
  - Formatted digests for email and messaging platforms

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

- **Gateway Agent**:
  - Submitting content via email while on the go
  - Sharing articles via WhatsApp for processing
  - Issuing commands through messaging platforms
  - Automated content intake from various channels
  - Centralized content submission interface

- **Digest Agent**:
  - Receiving daily summaries of processed content
  - Discovering thematic connections across content
  - Getting insights from accumulated knowledge
  - Scheduling regular content summary delivery
  - Creating custom digests for specific topics or time periods

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
```

### Setting Up Communication Gateways

#### Email Gateway Setup

##### Option 1: Password-Based Authentication (Basic Setup)

The easiest way to set up the email gateway with password-based authentication is using the provided setup script:

```bash
# Run the interactive setup script
./scripts/setup_email_gateway.sh
```

This will guide you through setting up an email account for receiving content.

Alternatively, you can manually configure it:

```bash
# Configure the email gateway with your settings
curl -X POST http://localhost:8080/gateway/email/config \
  -H "Content-Type: application/json" \
  -d '{
    "email_address": "your-email@gmail.com",
    "server": "imap.gmail.com",
    "password": "your-app-password",
    "port": 993,
    "use_ssl": true,
    "check_interval": 300,
    "outgoing_server": "smtp.gmail.com",
    "outgoing_port": 587,
    "outgoing_use_tls": true
  }'

# Start the email gateway
curl -X POST http://localhost:8080/gateway/email/start
```

##### Option 2: Google OAuth Authentication (Recommended for Google Workspace)

For Gmail or Google Workspace accounts, OAuth authentication is recommended:

1. Set up Google OAuth credentials in the Google Cloud Console
2. Configure Bluelabel AIOS with your credentials:

```bash
# Configure Google OAuth
curl -X POST "http://localhost:8080/gateway/google/config" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_GOOGLE_CLIENT_ID",
    "client_secret": "YOUR_GOOGLE_CLIENT_SECRET"
  }'

# Get authentication URL
curl "http://localhost:8080/gateway/google/auth"
```

3. Open the returned `auth_url` in your browser and complete the authentication
4. Configure and start the email gateway with OAuth:

```bash
# Configure and start the email gateway with OAuth
curl -X POST "http://localhost:8080/gateway/email/google"
```

See `docs/email_gateway_setup.md` and `docs/google_oauth_setup.md` for detailed instructions.

#### WhatsApp Gateway Setup

```bash
# Configure the WhatsApp gateway
curl -X POST http://localhost:8080/gateway/whatsapp/config \
  -H "Content-Type: application/json" \
  -d '{
    "phone_id": "your_phone_id",
    "business_account_id": "your_business_account_id",
    "api_token": "your_api_token",
    "verify_token": "your_verify_token",
    "enabled": true
  }'
```

### Configuring Digests

#### Scheduled Digests

```bash
# Schedule a daily digest delivered via email
curl -X POST http://localhost:8080/scheduler/digests \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_type": "daily",
    "time": "08:00",
    "recipient": "your-email@example.com",
    "digest_type": "daily",
    "delivery_method": "email",
    "content_types": ["url", "pdf", "text"],
    "tags": []
  }'
```

#### On-Demand Digests

```bash
# Generate a digest immediately for the last 7 days
curl -X POST http://localhost:8080/digests/generate \
  -H "Content-Type: application/json" \
  -d '{
    "digest_type": "weekly",
    "date_range": "2025-05-05,2025-05-12",
    "delivery_method": "email",
    "recipient": "your-email@example.com"
  }'
```

You can also manage digests through the Streamlit UI on the "Digest Management" page.
```

### Using the Gateway Agent

The Gateway agent allows you to process content by sending it to specific email addresses or WhatsApp numbers:

1. **Email Gateway**:
   - Send links, text, or attachments to your configured email address
   - Subject lines can contain commands or tags: `[TAG: tech, ai] Article for processing`
   - PDF and audio files can be sent as attachments
   - The Gateway will automatically process content and route it to the appropriate agent

2. **WhatsApp Gateway**:
   - Send messages to your configured WhatsApp number
   - Include links, text, or media in your messages
   - Use natural language commands: "Research quantum computing"
   - Request digests directly: "Send me a digest of AI content from this week"

### Using the Digest Agent

The Digest Agent can be used through the UI or API:

1. **Scheduled Digests**:
   - Configure daily, weekly, or monthly digests via the Digest Management page
   - Customize content types and tags to include
   - Select delivery method (email or WhatsApp)

2. **On-Demand Digests**:
   - Create custom digests for specific date ranges or topics
   - Filter by content type, tags, or keywords
   - View digests directly in the UI or have them delivered

3. **Digest Analysis**:
   - Explore themes and connections between content items
   - Discover insights that span multiple content sources
   - Use cross-references to understand relationships between topics

## Contributing

This is a personal project for now. Contribution guidelines may be added later.

## License

[License information to be determined]

# Flask UI and FastAPI Backend

This project consists of a Flask UI and a FastAPI backend. The Flask UI connects to the FastAPI backend to fetch and display data.

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\\Scripts\\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the backend:**
   - Ensure `server_config.json` is correctly set up with the FastAPI backend URL (e.g., `http://127.0.0.1:8081`).

## Running the Backend

Start the FastAPI backend:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8081 --reload
```

## Running the Flask UI

Start the Flask UI:
```bash
python3 flask_ui/app.py
```

Visit [http://127.0.0.1:8080/](http://127.0.0.1:8080/) to see the dashboard.

## Running Tests

Run tests using pytest:
```bash
pytest
```

## Project Structure

- `flask_ui/`: Contains the Flask UI code.
- `app/`: Contains the FastAPI backend code.
- `server_config.json`: Configuration file for the Flask UI.

## Notes

- Debug print statements have been removed for production.
- Ensure no sensitive data is included in configuration files.