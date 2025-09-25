# Kiu Journeys Search API

A Django REST API for flight journey search with hexagonal architecture and Docker support.

## 🎯 Overview

This API allows searching for flight journeys between cities on specific dates. It supports both direct flights (1 flight) and connecting flights (2 flights) with intelligent connection validation.

## ✨ Features

- 🐳 **Dockerized**: Ready to run with Docker and docker-compose
- 🏗️ **Hexagonal Architecture**: Clean separation of concerns with DI container
- 📚 **Swagger Documentation**: Interactive API documentation with OpenAPI 2.0
- 🚫 **No Database**: Stateless API without database dependencies
- 🔓 **No Authentication**: Simple API without user management
- 🌍 **UTC Time Handling**: Built-in UTC time management
- ✈️ **Journey Search**: Find direct and connecting flights
- 🔗 **Connection Validation**: Smart connection time and duration checks
- 🧪 **Fully Tested**: Comprehensive test suite

## 🚀 Quick Start

### 🐳 Using Docker (Recommended)

Docker comes pre-configured with all necessary environment variables.

```bash
# Build and start the service
docker-compose up --build

# Run in background
docker-compose up --build -d

# Stop the service
docker-compose down
```

**API will be available at:** http://localhost:8000

### 📚 API Documentation

The API includes interactive documentation powered by Swagger/OpenAPI:

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **OpenAPI JSON**: http://localhost:8000/swagger.json
- **OpenAPI YAML**: http://localhost:8000/swagger.yaml

### 💻 Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   # Copy and edit the example file
   cp env.example .env
   # Edit .env with your values
   
   # Start the server
   python manage.py runserver
   ```

3. **Run tests:**
   ```bash
   # All tests
   python -m pytest
   
   # Specific test file
   python -m pytest journey/di/test_container.py -v
   ```

## 📡 API Documentation

### Journey Search Endpoint

**GET** `/journey/search/`

Search for flight journeys between two cities on a specific date.

#### Parameters

| Parameter | Type | Required | Format | Description |
|-----------|------|----------|---------|-------------|
| `date` | string | ✅ | `YYYY-MM-DD` | Search date |
| `from` | string | ✅ | `XXX` | Origin city code (3 letters) |
| `to` | string | ✅ | `XXX` | Destination city code (3 letters) |

#### Example Request

```bash
curl "http://localhost:8000/journey/search/?date=2024-09-13&from=MAD&to=PMI"
```

#### Using Swagger Documentation

For interactive testing and detailed API documentation:

1. **Open Swagger UI**: http://localhost:8000/swagger/
2. **Find the endpoint**: Look for "Journey Search" section
3. **Click "Try it out"** on the `/journey/search/` endpoint
4. **Enter parameters**:
   - `date`: `2024-12-25`
   - `from`: `MAD`
   - `to`: `BCN`
5. **Click "Execute"** to test the API
6. **View response** with detailed examples and error codes

The Swagger documentation includes:
- ✅ **Interactive testing** - Test endpoints directly from the browser
- ✅ **Request/response examples** - See exact JSON formats
- ✅ **Parameter validation** - Understand required fields and formats
- ✅ **Error documentation** - Learn about possible error responses
- ✅ **Business rules** - Understand v1.0 limitations and constraints

#### Response Format

```json
[
  {
    "connections": 0,
    "path": [
      {
        "flight_number": "XX1234",
        "from": "MAD",
        "to": "PMI",
        "departure_time": "2024-09-13 10:00",
        "arrival_time": "2024-09-13 11:30"
      }
    ]
  },
  {
    "connections": 1,
    "path": [
      {
        "flight_number": "XX1234",
        "from": "MAD",
        "to": "BCN",
        "departure_time": "2024-09-13 08:00",
        "arrival_time": "2024-09-13 09:15"
      },
      {
        "flight_number": "XX5678",
        "from": "BCN",
        "to": "PMI",
        "departure_time": "2024-09-13 11:00",
        "arrival_time": "2024-09-13 12:15"
      }
    ]
  }
]
```

#### Response Fields

- `connections`: Number of connections (0 = direct flight, 1 = one connection)
- `path`: Array of flight events in the journey
- `flight_number`: Flight identifier
- `from`/`to`: Airport/city codes
- `departure_time`/`arrival_time`: UTC timestamps in `YYYY-MM-DD HH:MM` format

#### Error Responses

**400 Bad Request** - Invalid parameters:
```json
{
  "errors": {
    "date": ["Date has wrong format. Use YYYY-MM-DD."],
    "from_param": ["This field is required."]
  }
}
```

**500 Internal Server Error** - Server error:
```json
{
  "error": "Internal server error",
  "message": "Unable to fetch flight data"
}
```

## 🏗️ Architecture

### Hexagonal Architecture (Ports & Adapters)

```
journey/
├── core/                    # 🧠 Domain Layer
│   ├── entities/
│   │   └── flight_event.py  # FlightEvent, Journey entities
│   ├── services/
│   │   └── journey_service.py # Business logic
│   ├── interfaces.py        # Domain interfaces
│   └── config.py           # Business rules & v1.0 limitations
│
├── infrastructure/          # 🌐 Infrastructure Layer
│   ├── adapters/
│   │   └── flight_api_adapter.py # External API integration
│   └── serializers/
│       └── journey_serializer.py # Request/response serialization
│
├── app/                     # 🎯 Application Layer
│   ├── views.py            # API endpoints
│   ├── urls.py             # URL routing
│   └── tests/              # Application tests
│
└── di/                      # 🏗️ Dependency Injection
    ├── container.py        # DI container
    └── test_container.py   # DI tests
```

### Business Rules (v1.0)

#### Journey Constraints
- **Maximum flights per journey:** 2 (v1.0 limitation)
- **Maximum total duration:** 24 hours
- **Maximum connection time:** 4 hours between flights
- **Connection validation:** Destination of first flight must match origin of second flight

#### Future Versions
- **v2.0+:** Support for multi-leg journeys (3+ flights)
- **v2.0+:** Configurable connection time limits
- **v2.0+:** Support for overnight connections
- **v2.0+:** Different journey types (business, leisure)

## ⚙️ Configuration

### Django Dependencies for Swagger

This API includes Swagger/OpenAPI documentation, which requires additional Django components that are not typically needed for a minimal API:

#### Required Django Apps
- `django.contrib.auth` - User authentication (required by admin)
- `django.contrib.messages` - Message framework (required by admin)
- `django.contrib.staticfiles` - Static file serving (required by drf-yasg)
- `django.contrib.admin` - Admin interface (provides templates for drf-yasg)

#### Required Middleware
- `django.contrib.sessions.middleware.SessionMiddleware`
- `django.contrib.auth.middleware.AuthenticationMiddleware`
- `django.contrib.messages.middleware.MessageMiddleware`

#### Database Configuration
- **In-memory SQLite** database (`:memory:`) for minimal overhead
- No persistent data storage
- Required for Django admin templates

#### Considerations
- These dependencies add minimal overhead since no actual authentication or admin functionality is used
- The database is in-memory and requires no setup or migrations
- All admin-related functionality is disabled in practice
- Static files are served for Swagger UI assets only

### Environment Variables

| Variable | Default | Docker Value | Description | Required |
|----------|---------|--------------|-------------|----------|
| `DEBUG` | `False` | `True` | Enable debug mode | Optional |
| `SECRET_KEY` | None | `kiu-journeys-dev-secret-key-...` | Django secret key | ✅ |
| `ALLOWED_HOSTS` | None | `localhost,127.0.0.1,0.0.0.0,*` | Allowed hosts | ✅ |
| `FLIGHT_API_URL` | Mock API | Mock API | External flight events API | Optional |
| `FLIGHT_API_TIMEOUT` | `30` | `30` | API timeout in seconds | Optional |

### Security Features

- ✅ **Production-first:** DEBUG defaults to `False`
- ✅ **No defaults:** SECRET_KEY and ALLOWED_HOSTS must be set
- ✅ **Environment-based:** Docker and .env file support
- ✅ **Fail-fast:** Won't start without required variables

## 🧪 Testing

### Run Tests

```bash
# Using Docker
docker-compose exec web python -m pytest -v

# Local development
python -m pytest -v

# Specific test files
python -m pytest journey/di/test_container.py -v
```

### Test Coverage

- ✅ **DI Container:** Singleton/Factory patterns, configuration
- ✅ **Domain Entities:** Business rule validation
- ✅ **Journey Service:** Search logic
- ✅ **API Integration:** End-to-end journey search

## 🔧 Development

### Adding New Features

1. **Domain Logic:** Add to `journey/core/`
2. **External Services:** Add adapters to `journey/infrastructure/adapters/`
3. **API Endpoints:** Add to `journey/app/views.py`
4. **Dependencies:** Register in `journey/di/container.py`

### Version Limitations

Current version (v1.0) has the following limitations documented in code:

- `MAX_FLIGHTS_PER_JOURNEY = 2`
- `MAX_JOURNEY_DURATION_HOURS = 24`
- `MAX_CONNECTION_TIME_HOURS = 4`

These are easily configurable for future versions in `journey/core/config.py`.

## 📚 External Dependencies

### API Dependencies
- **Flight Events API:** https://mock.apidog.com/m1/814105-793312-default/flight-events
- **Django REST Framework:** API framework
- **aiohttp:** Async HTTP client for external API calls
- **drf-yasg:** Swagger/OpenAPI documentation for Django REST Framework

### Development Dependencies
- **pytest:** Testing framework
- **pytest-django:** Django integration for pytest
- **pytest-asyncio:** Async test support
- **freezegun:** Time mocking for tests
- **python-dotenv:** Environment variable loading

## 🚀 Deployment

The application is production-ready with:
- Environment-based configuration
- Stateless design (no database)
- Docker containerization
- Proper error handling and logging
- Security best practices
- Interactive API documentation

### Production Considerations

#### Swagger Documentation
- **Development**: Swagger UI is accessible at `/swagger/` and `/redoc/`
- **Production**: Consider restricting access to documentation endpoints if needed
- **Security**: No authentication is required for API or documentation (by design)
- **Performance**: Minimal overhead from in-memory database and static file serving

#### Static Files
- Static files are served by Django for Swagger UI assets
- For production, consider using a dedicated static file server (nginx, CDN)
- Static files are located at `/static/drf-yasg/`

#### Database
- Uses in-memory SQLite (`:memory:`) for Django admin dependencies
- No persistent storage or migrations required
- Automatically recreated on each application restart

For production deployment, ensure all required environment variables are properly set and use a production-grade WSGI server.