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
- ⚡ **Redis Caching**: Intelligent caching to reduce external API calls
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

**Note:** Past date validation is currently disabled for testing purposes since the external API only returns historical data from 2021-12-31. Future versions should include past date validation to reject queries for dates before today.

#### Parameters

| Parameter | Type | Required | Format | Description |
|-----------|------|----------|---------|-------------|
| `date` | string | ✅ | `YYYY-MM-DD` | Search date |
| `from` | string | ✅ | `XXX` | Origin city code (3 letters) |
| `to` | string | ✅ | `XXX` | Destination city code (3 letters) |

#### Example Request

**Working Example with Real Data:**
```bash
curl "http://localhost:8000/journey/search/?date=2021-12-31&from=MAD&to=BUE"
```

**With Pretty Print:**
```bash
curl -s "http://localhost:8000/journey/search/?date=2021-12-31&from=MAD&to=BUE" | python -m json.tool
```

**Expected Response:**
```json
[
    {
        "connections": 0,
        "path": [
            {
                "flight_number": "IB1234",
                "from": "MAD",
                "to": "BUE",
                "departure_time": "2021-12-31 23:59",
                "arrival_time": "2022-01-01 12:00"
            }
        ]
    }
]
```

**Other Working Examples:**
```bash
# Test different dates (will return empty if no flights available)
curl "http://localhost:8000/journey/search/?date=2025-12-31&from=MAD&to=BUE"

# Test different routes
curl "http://localhost:8000/journey/search/?date=2021-12-31&from=BUE&to=MAD"
```

#### Using Swagger Documentation

For interactive testing and detailed API documentation:

1. **Open Swagger UI**: http://localhost:8000/swagger/
2. **Find the endpoint**: Look for "Journey Search" section
3. **Click "Try it out"** on the `/journey/search/` endpoint
4. **Enter parameters** (using real available data):
   - `date`: `2021-12-31`
   - `from`: `MAD`
   - `to`: `BUE`
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

#### Performance Optimization Roadmap

**External API Optimization:**
- **Filtered API Calls:** Investigate if external flight APIs support filtering by date, origin, and destination to reduce data transfer and improve response times
- **Query Parameters:** Implement selective data fetching instead of downloading all flight events for a date
- **Network Efficiency:** Analyze API response patterns to minimize bandwidth usage

**Advanced Caching Strategy:**
- **Smart Cache Schema:** Analyze search patterns to identify most common city/date combinations
- **Selective Caching:** Cache only frequently requested routes rather than all possible combinations
- **Memory Management:** Implement cache eviction policies based on usage frequency and recency
- **Cache Warming:** Pre-populate cache with popular routes during low-traffic periods
- **Distributed Caching:** Consider cache sharding for high-volume scenarios

**Analytics & Monitoring:**
- **Search Pattern Analysis:** Track most common origin/destination pairs and dates
- **Cache Hit Ratio Monitoring:** Measure cache effectiveness and optimize TTL values
- **API Response Time Tracking:** Monitor external API performance and identify bottlenecks
- **Memory Usage Analytics:** Track Redis memory consumption patterns for optimization

**Implementation Strategy:**
- **Phase 1:** Implement search pattern logging and basic analytics
- **Phase 2:** Analyze collected data to identify top 20% most requested routes
- **Phase 3:** Implement selective caching for popular routes only
- **Phase 4:** Investigate external API filtering capabilities
- **Phase 5:** Implement filtered API calls and advanced cache eviction policies

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

#### Cache Configuration
The API includes a Redis-based caching system to improve performance and reduce external API calls:

**Environment Variables:**
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`)
- `CACHE_TTL`: Cache time-to-live in seconds (default: `3600` = 1 hour)

**Cache Behavior:**
- Flight events are cached by date with configurable TTL
- Cache-first strategy: checks cache before making external API calls
- Automatic cache population after successful API responses
- Graceful fallback to API when cache is unavailable

**Docker Setup:**
- Redis service included in `docker-compose.yml`
- Automatic volume persistence for cache data
- Pre-configured connection between web and Redis services

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

### Cache Dependencies
- **Redis:** In-memory data structure store for caching
- **aioredis:** Async Redis client for Python
- **redis:** Redis Python client (synchronous operations)

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

#### Redis Cache
- **Production Setup**: Configure `REDIS_URL` to point to your production Redis instance
- **High Availability**: Consider Redis Cluster or Redis Sentinel for production
- **Memory Management**: Monitor Redis memory usage and configure eviction policies
- **Cache TTL**: Adjust `CACHE_TTL` based on your data freshness requirements
- **Backup Strategy**: Implement Redis persistence (RDB/AOF) for cache durability
- **Security**: Configure Redis authentication and network access controls

For production deployment, ensure all required environment variables are properly set and use a production-grade WSGI server.