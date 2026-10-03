# 🤖 RAG Chatbot — AI Customer Support & Lead Intelligence

> **Summer Internship Project at INFOTECHMON PVT. LTD.**

A full-stack **Retrieval-Augmented Generation (RAG) chatbot** built to provide intelligent, document-grounded customer support while also supporting **intent classification, automated lead capture, lead scoring, conversation memory, feedback analysis, and administrative analytics**.

The application combines a **React + TypeScript frontend**, **FastAPI backend**, **FAISS vector search**, **MongoDB Atlas**, and configurable **Google Gemini / OpenAI models**.

---

## 🚀 Live Demo

> [Click here to View.](https://rag-chatbot-three-pi.vercel.app/)

---

## 📌 Project Overview

Traditional chatbots rely primarily on an LLM's pre-trained knowledge, which can result in outdated, generic, or unsupported answers.

This project implements a **Retrieval-Augmented Generation (RAG)** architecture where the chatbot retrieves relevant information from an organization's knowledge base before generating a response.

The system also extends beyond basic question answering by providing:

- 📚 Document-based knowledge retrieval
- 🧠 Conversational memory
- 🎯 Intent classification
- 👤 Automated lead extraction
- 📊 Lead scoring
- 🔐 Authentication and role-based access
- 📈 Admin analytics
- 👍 User feedback tracking
- 📄 Multi-format document ingestion

---

# ✨ Key Features

## 📚 RAG-Based Question Answering

- Retrieves relevant information from uploaded organizational documents.
- Uses **FAISS vector similarity search**.
- Provides retrieved source information along with generated answers.
- Uses configurable **Gemini / OpenAI LLMs**.
- Helps reduce hallucination by grounding responses in the organization's knowledge base.

---

## 📄 Multi-Format Document Ingestion

Administrators can upload:

- PDF
- DOCX
- TXT

The ingestion pipeline:

```text
Document Upload
      ↓
Text Extraction
      ↓
Document Chunking
      ↓
Embedding Generation
      ↓
FAISS Vector Index
      ↓
Ready for Retrieval
```

Current chunking configuration:

```text
Chunk Size    : 500 characters
Chunk Overlap : 50 characters
```

---

## 🧠 Conversational Memory

The chatbot maintains session-based conversation history to provide contextual responses to follow-up questions.

Example:

```text
User: What services do you provide?

Bot: We provide AI and software development services...

User: Which one is suitable for startups?

Bot: Based on the services we discussed earlier...
```

---

## 🎯 Intelligent Intent Classification

User queries are classified into operational categories:

| Intent | Purpose |
|---|---|
| 🛠️ Support | Technical assistance and troubleshooting |
| 💰 Sales | Product/service interest and demo inquiries |
| 💳 Pricing | Pricing, plans and billing-related queries |
| ⚠️ Complaint | Dissatisfaction, issues and complaints |

The system uses LLM-based classification with a keyword-based fallback mechanism.

---

## 👤 Automated Lead Capture

Sales and pricing conversations can trigger automated lead processing.

The system attempts to extract:

- Name
- Email
- Company / Organization

Lead information is then stored in **MongoDB Atlas**.

---

## 📊 Lead Scoring

The system calculates a lead score from **0–100** using conversation signals such as:

- User intent
- Email availability
- Company information
- User name
- Conversation engagement

Example categorization:

```text
70–100  → Hot Lead
30–69   → Warm Lead
0–29    → Cold Lead
```

---

## 🔐 Authentication & Role-Based Access

The application supports:

- User registration
- User login
- Logout
- JWT-based authentication
- Password hashing
- HTTP-only authentication cookies
- Role-based authorization

Supported roles:

```text
User
Admin
```

Administrative functionality is protected using role-based access control.

---

## 🖥️ Admin Operations Console

Administrators can monitor the chatbot through a dedicated dashboard.

The dashboard provides:

- Total conversations
- Conversation turns
- Intent distribution
- User feedback metrics
- Leads captured
- Lead scores
- Lead intent
- Lead information
- Lead filtering and sorting
- Document ingestion
- Analytics refresh

---

## 👍 User Feedback

Users can provide feedback on chatbot responses.

The system tracks:

- Total feedback
- Positive feedback
- Negative feedback
- Feedback statistics

This information is available through the admin analytics dashboard.

---

# 🏗️ System Architecture

```text
                         ┌──────────────────────┐
                         │       USER           │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │     React + TypeScript      │
                    │       Frontend              │
                    │                             │
                    │  Login │ Chat │ Admin       │
                    └──────────────┬──────────────┘
                                   │
                                   │ REST API
                                   ▼
                    ┌─────────────────────────────┐
                    │        FastAPI Backend      │
                    │                             │
                    │ ┌──────┐ ┌──────┐ ┌──────┐ │
                    │ │ Auth │ │ Chat │ │ Docs │ │
                    │ └──────┘ └──┬───┘ └──┬───┘ │
                    │              │        │     │
                    │       ┌──────▼────────▼───┐ │
                    │       │    RAG Engine      │ │
                    │       └─────────┬─────────┘ │
                    └─────────────────┼───────────┘
                                      │
                 ┌────────────────────┼────────────────────┐
                 │                    │                    │
                 ▼                    ▼                    ▼
        ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
        │ Gemini /       │   │ FAISS Vector   │   │ MongoDB Atlas  │
        │ OpenAI         │   │ Database       │   │                │
        │ LLM            │   │                │   │ Users / Leads  │
        └────────────────┘   └────────────────┘   │ Chats / Stats  │
                                                   └────────────────┘
```

---

# 🔄 RAG Pipeline

```text
┌───────────────────┐
│   User Question   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Intent Detection  │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Query Embedding   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ FAISS Similarity  │
│     Search        │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Top Relevant      │
│ Document Chunks   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Conversation      │
│ Context / Memory  │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Gemini / OpenAI   │
│      LLM          │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Grounded Answer   │
│ + Source Data     │
└───────────────────┘
```

---

# 📈 Lead Intelligence Pipeline

```text
                 User Message
                      │
                      ▼
              Intent Classification
                      │
          ┌───────────┼───────────┐
          │           │           │
       Support      Sales       Pricing
          │           │           │
          │           └─────┬─────┘
          │                 │
          │                 ▼
          │          Lead Extraction
          │                 │
          │       ┌─────────┼─────────┐
          │       ▼         ▼         ▼
          │     Name      Email    Company
          │       │         │         │
          │       └─────────┼─────────┘
          │                 ▼
          │           Lead Scoring
          │                 │
          │                 ▼
          │          MongoDB Atlas
          │                 │
          │                 ▼
          └──────────► Admin Dashboard
```

---

# 🛠️ Technology Stack

## Frontend

| Technology | Purpose |
|---|---|
| React | UI development |
| TypeScript | Type-safe frontend development |
| Vite | Frontend build tooling |
| React Router | Client-side routing |
| Tailwind CSS | UI styling |
| Axios | API communication |
| Recharts | Analytics visualization |
| Lucide React | UI icons |

---

## Backend

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| Pydantic | Data validation |
| Python-JOSE | JWT handling |
| Passlib / bcrypt | Password hashing |
| Python-dotenv | Environment configuration |

---

## AI / RAG

| Technology | Purpose |
|---|---|
| LangChain | RAG pipeline and document processing |
| FAISS | Vector similarity search |
| Google Gemini | LLM / embeddings |
| OpenAI | LLM / embeddings fallback |
| Gemini Embeddings | Document/query vectorization |

---

## Database

| Technology | Purpose |
|---|---|
| MongoDB Atlas | Cloud application database |
| FAISS | Local vector index |

MongoDB Atlas stores application data such as:

- Users
- Conversations
- Leads
- Feedback
- Analytics-related information

---

## Document Processing

- PyPDF
- Docx2txt
- LangChain document loaders
- Recursive Character Text Splitter

---

# 💻 Installation

## Prerequisites

Make sure you have:

- Python 3.10+
- Node.js
- npm
- MongoDB Atlas account
- Git

---

## 1. Clone the Repository

```bash
git clone https://github.com/dushyantrajotia/RAG-chatbot.git
cd RAG-chatbot
```

---

## 2. Create Python Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Install Frontend Dependencies

```bash
npm install
```

---

## 5. Configure Environment Variables

Create the `.env` file and configure:

```text
GEMINI_API_KEY
OPENAI_API_KEY
MONGO_URI
JWT_SECRET
JWT_ALGORITHM
FRONTEND_ORIGIN
```

---

# ▶️ Running the Application

The project consists of a FastAPI backend and React frontend.

## Start Backend

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Start Frontend

Open another terminal:

```bash
npm run dev
```

The Vite development server will provide the frontend URL in the terminal.

---

# 👨‍💻 Application Workflow

## User Workflow

```text
Register / Login
       ↓
Open Chat
       ↓
Ask Question
       ↓
Intent Classification
       ↓
Retrieve Relevant Knowledge
       ↓
Generate AI Response
       ↓
Display Answer + Sources
       ↓
Collect Feedback
```

---

## Admin Workflow

```text
Admin Login
     ↓
Admin Dashboard
     ↓
Upload Knowledge Documents
     ↓
Document Processing
     ↓
FAISS Index Creation / Update
     ↓
Monitor Conversations
     ↓
Review Leads
     ↓
Analyze Intent & Feedback
```

---

# 🔐 Security

The application implements:

- Password hashing using bcrypt
- JWT-based authentication
- HTTP-only authentication cookies
- Role-based access control
- Protected API endpoints
- Admin-only document ingestion
- Admin-only analytics and lead access
- Environment-based secret configuration

For production deployment, additional security hardening should be considered:

- HTTPS-only cookies
- Secure secret management
- Production CORS configuration
- API rate limiting
- Input validation and sanitization
- Database access controls
- Monitoring and logging

---

# 🔮 Future Enhancements

## RAG Improvements

- Hybrid BM25 + vector retrieval
- Semantic reranking
- Metadata filtering
- Query rewriting
- Context compression
- Automated RAG evaluation
- Retrieval precision/recall benchmarking

## Business Intelligence

- CRM integration
- Lead conversion tracking
- Email notifications
- Sales pipeline management
- Customer segmentation
- Advanced lead prioritization

## AI Capabilities

- Multi-agent workflows
- Tool calling
- Function-based actions
- Human-agent escalation
- Multilingual support
- Voice-based interaction

## Infrastructure

- Dockerized deployment
- Cloud-based vector database
- CI/CD pipeline
- Centralized logging
- Application monitoring
- Scalable backend architecture

---

# 📚 Learning Outcomes

This internship project provided practical experience in:

- Retrieval-Augmented Generation
- Large Language Model integration
- Vector similarity search
- FAISS
- Prompt engineering
- Document processing
- Conversational AI
- FastAPI
- React + TypeScript
- REST API development
- MongoDB Atlas
- JWT authentication
- Role-based authorization
- Intent classification
- Lead extraction
- Lead scoring
- Data visualization
- Full-stack AI application development

---

# 🏢 Internship

## Summer Internship at INFOTECHMON PVT. LTD.

This project was developed as part of my **Summer Internship at INFOTECHMON PVT. LTD.**, focusing on the practical implementation of **Generative AI, Retrieval-Augmented Generation, full-stack development, and AI-powered customer support systems**.

---

# 👨‍💻 Author

**Dushyant & Manul Sahu**

B.Tech — Computer Science & Engineering  
AI / ML & Full-Stack Development

### GitHub

[![GitHub](https://img.shields.io/badge/GitHub-Dushyant%20Rajotia-black?style=for-the-badge&logo=github)](https://github.com/dushyantrajotia)
[![GitHub](https://img.shields.io/badge/GitHub-Manul%20Sahu-black?style=for-the-badge&logo=github)](https://github.com/manulsahu)

---

# 📄 License

This project is developed for educational, internship, and portfolio purposes.
