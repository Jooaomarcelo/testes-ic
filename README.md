# Campo Vertentes | Coffee API

## Description

Este repositório serve como estudo e experimentação das tecnologias utilizadas para desenvolvimento de uma aplicação final. Campo Vertentes Coffee API é uma API RESTful construída com FastAPI, MongoDB e Docker, fornecendo endpoints para gerenciamento de dados relacionados a café com recursos de autenticação e autorização. O projeto também implementa processamento assíncrono de tarefas utilizando Celery com RabbitMQ como broker de mensagens e Redis como backend de resultados.

> **Nota:** Este é um projeto de estudo para explorar e aprender as tecnologias que serão aplicadas no desenvolvimento da aplicação final do projeto de Iniciação Científica.

## Features

- 🔐 JWT-based authentication
- ☕ Coffee management endpoints
- 👥 User management
- 🐳 Docker containerization
- 📝 Automatic API documentation
- 🔒 OAuth2 security implementation
- ⚙️ Celery for asynchronous task processing

## Tech Stack

- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database
- **Docker** - Containerization
- **Pydantic** - Data validation
- **JWT** - Token-based authentication
- **Celery** - Distributed task queue for asynchronous processing
- **RabbitMQ** - Message broker for Celery
- **Redis** - Result backend for Celery tasks

## How to Run

### Prerequisites

- Docker
- Docker Compose

### Steps

1. Clone the repository:

```bash
git clone https://github.com/Jooaomarcelo/fast-api-project
cd backend-python
```

2. Start the application with Docker Compose:

```bash
docker-compose up -d
```

3. Access the API documentation at:

```
http://localhost:{PORT}/docs
```

4. To stop the application:

```bash
docker-compose down
```

## Development

For development mode, you can use:

```bash
docker-compose -f docker-compose.yml up
```

For production mode:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Project Structure

```
backend-python/
├── src/
│   ├── core/          # Core configurations and security
│   ├── models/        # Data models
│   ├── repos/         # Repository layer
│   ├── routers/       # API endpoints
│   ├── services/      # Business logic
│   └── utils/         # Utility functions
├── docker/            # Docker configuration files
└── requirements.txt   # Python dependencies
```

## API Endpoints

- `/docs` - Interactive API documentation (Swagger UI)
- `/redoc` - Alternative API documentation
- `/auth` - Authentication endpoints
- `/users` - User management endpoints
- `/coffee` - Coffee management endpoints
