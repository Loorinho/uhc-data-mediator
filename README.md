# UHC Data Mediator

A full-stack application with a Django REST API, a TanStack Start frontend, and PostgreSQL — all run with Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin
- Git

## Getting Started

1. **Clone the repository**

   ```bash
   git clone git@github.com:Loorinho/uhc-data-mediator.git
   cd uhc-data-mediator
   ```

2. **Create your environment file**

   ```bash
   cp .env.example .env
   ```

   Adjust the values in `.env` if needed.

3. **Build the images**

   ```bash
   docker compose build
   ```

4. **Start the application**

   ```bash
   docker compose up -d
   ```

## Application URLs

| Service      | URL                                  |
| ------------ | ------------------------------------ |
| Frontend     | http://localhost:3000                |
| API          | http://localhost:8000/api/v1/        |
| Django admin | http://localhost:8000/admin/         |
