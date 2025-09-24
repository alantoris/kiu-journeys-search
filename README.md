# Kiu Journeys Search API

A minimal Django REST API for journey search functionality with Docker support.

## Features

- 🐳 **Dockerized**: Ready to run with Docker and docker-compose
- 🚫 **No Database**: Stateless API without database dependencies
- 🔓 **No Authentication**: Simple API without user management
- 🌍 **UTC Time Handling**: Built-in UTC time management with timezone conversion support

## Quick Start

### 🐳 Using Docker (Recommended for Development)

Docker comes pre-configured with all necessary environment variables in `docker-compose.yml`.

```bash
# Build and start the service
docker-compose up --build

# Run in background (detached mode)
docker-compose up --build -d

# Stop the service
docker-compose down
```

**API Base URL:**
- Journey endpoints: http://localhost:8000/journey/

> **Note:** All environment variables are explicitly set in `docker-compose.yml` - no defaults are used.

### 💻 Local Development (Without Docker)

For local development without Docker, you **must** provide environment variables. No defaults are used.

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables (choose one method):**

   **Option A: Using .env file (Recommended)**
   ```bash
   # Copy the example file and edit it
   cp env.example .env
   # Edit .env with your preferred values
   
   # The .env file will be automatically loaded
   python manage.py runserver
   ```

   **Option B: Using environment variables directly**
   ```bash
   export DEBUG=True
   export SECRET_KEY=your-secret-key-here-minimum-50-characters
   export ALLOWED_HOSTS=localhost,127.0.0.1
   
   python manage.py runserver
   ```

3. **Access the API:**
   - Journey endpoints: http://localhost:8000/journey/

> **Important:** All environment variables (`SECRET_KEY`, `ALLOWED_HOSTS`) are **required**. The application will fail to start without them.

## API Endpoints

### Journey Endpoints
- Base URL: `/journey/`
- Ready for journey search implementation

> **Note:** Journey search endpoints will be implemented here. The URL structure is now organized with journey-specific endpoints under `/journey/`.

## Project Structure

```
kiu-journeys-search/
├── kiu_journeys_search/    # Django project settings
├── journey/                # Journey app
│   ├── views.py           # API endpoints
│   └── urls.py            # URL routing
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
└── README.md              # This file
```

## Configuration

### Environment Variables

| Variable | Default | Docker Value | Description | Required |
|----------|---------|--------------|-------------|----------|
| `DEBUG` | `False` (production-safe) | `True` | Enable/disable debug mode | Optional |
| `SECRET_KEY` | None | `kiu-journeys-dev-secret-key-...` | Django secret key | ✅ |
| `ALLOWED_HOSTS` | None | `localhost,127.0.0.1,0.0.0.0,*` | Comma-separated allowed hosts | ✅ |

### Security Features

- ✅ **Production-first defaults**: DEBUG defaults to `False` (production-safe)
- ✅ **No secret defaults**: SECRET_KEY and ALLOWED_HOSTS must be explicitly set
- ✅ **Environment-based configuration**: Docker and .env file support
- ✅ **Fail-fast approach**: Application won't start without required variables
- ✅ **Development override**: Docker-compose explicitly enables DEBUG for development

### Project Configuration

The project is configured to:
- Handle all dates in UTC timezone
- Support CORS for frontend integration
- Use JSON-only API responses
- Skip unnecessary Django features (admin, auth, sessions)

## Development Notes

- Dates are handled in UTC for mathematical operations
- City codes can be used for timezone conversion (to be implemented)
- No database migrations needed
- No static files or templates required
