# AI Recruiter Agent

An intelligent recruiter agent system that combines email automation with resume processing capabilities. The application features a Python FastAPI backend for email operations and AI-powered workflows, paired with a Next.js frontend for user interaction.

## Features

- **Email Automation**: AI-powered email drafting and enhancement using LangGraph workflows
- **Gmail Integration**: Full Gmail API integration for sending and managing emails
- **Resume Processing**: Upload and analyze resumes against job descriptions
- **Human-in-the-Loop**: Interactive approval system for email content before sending
- **Modern UI**: Next.js frontend with Tailwind CSS for a clean, responsive interface

## Project Structure

```
recruiter-agent/
├── main.py              # LangGraph email workflow system
├── server.py            # FastAPI server with Gmail & resume processing
├── gmail_tools.py       # Gmail API integration utilities
├── frontend/            # Next.js frontend application
│   ├── package.json
│   └── src/
├── api/                 # API services
├── db/                  # Database schema and setup
├── resumes/             # Resume upload directory
└── templates/           # HTML templates
```

## Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn
- Gmail API credentials (for email functionality)

## Setup Instructions

### 1. Backend Setup (Required First)

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   # Add Gmail API credentials as needed
   ```

3. **Gmail API Setup** (if using email features):
   - Set up Gmail API credentials in Google Cloud Console
   - Download credentials file and configure as per `gmail_tools.py`

### 2. Frontend Setup

1. **Navigate to Frontend Directory**:
   ```bash
   cd frontend
   ```

2. **Install Node.js Dependencies**:
   ```bash
   npm install
   ```

## Running the Application

**IMPORTANT**: The backend must be started before the frontend for the application to work properly.

### Step 1: Start the Backend Server

Choose one of the following backend servers:

**Option A: FastAPI Server (Recommended for full features)**
```bash
python server.py
```
The server will start on `http://localhost:8000`

**Option B: LangGraph Workflow (for email workflow testing)**
```bash
python main.py
```

### Step 2: Start the Frontend Development Server

In a new terminal window:

```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3000`

### Accessing the Application

1. **Frontend Interface**: Navigate to `http://localhost:3000`
2. **Backend API**: Access API documentation at `http://localhost:8000/docs`
3. **Health Check**: Verify backend status at `http://localhost:8000/health`

## API Endpoints

The FastAPI backend provides the following key endpoints:

- `GET /` - Main application interface
- `GET /auth/status` - Gmail authentication status
- `POST /send-email/` - Send emails via Gmail
- `POST /search-emails/` - Search Gmail messages
- `POST /api/process-resume` - Process resume against job description
- `GET /api/resumes` - List uploaded resumes

## Usage

### Email Workflow

1. **LangGraph Workflow** (`main.py`):
   - Interactive email drafting and enhancement
   - Human-in-the-loop approval system
   - AI-powered content generation with Groq

2. **API-based Email** (via frontend):
   - Gmail integration for sending emails
   - Email management and search capabilities

### Resume Processing

1. Upload resume files to the `resumes/` directory
2. Use the frontend interface to process resumes against job descriptions
3. Get AI-powered analysis and recommendations

## Development

### Backend Development

- **FastAPI Server**: Modify `server.py` for API endpoints
- **Email Workflows**: Update `main.py` for LangGraph workflows
- **Gmail Integration**: Configure `gmail_tools.py` for email operations

### Frontend Development

- **Next.js App**: Frontend code in `frontend/src/`
- **Components**: React components for UI elements
- **API Integration**: Services for backend communication

### Adding New Features

1. **Backend**: Add new endpoints in `server.py`
2. **Frontend**: Create new pages/components in `frontend/src/`
3. **Workflows**: Extend LangGraph workflows in `main.py`

## Authentication

The application supports Gmail OAuth2 authentication:

1. Visit the application root to check authentication status
2. Follow the OAuth2 flow if not authenticated
3. Permissions include email sending and reading capabilities

## Troubleshooting

### Common Issues

1. **Frontend API Errors**: Ensure the backend server is running first
2. **Gmail Authentication**: Check API credentials and OAuth2 setup
3. **Resume Upload**: Verify the `resumes/` directory exists and has write permissions

### Port Conflicts

- Backend: Default port 8000 (configurable in `server.py`)
- Frontend: Default port 3000 (configurable in `frontend/package.json`)

## Dependencies

### Backend
- **FastAPI**: Web framework for the API
- **LangChain & LangGraph**: AI workflow orchestration
- **Groq**: AI model integration
- **Gmail API**: Email operations
- **Uvicorn**: ASGI server

### Frontend
- **Next.js**: React framework
- **React**: UI library
- **Tailwind CSS**: Styling framework
- **Axios**: HTTP client for API calls

## License

This project is provided for educational and development purposes.
