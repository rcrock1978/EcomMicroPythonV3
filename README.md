# Ecommerce Microservices Platform

This project implements a scalable ecommerce platform using microservices architecture with Django (backend) and Next.js (frontend), following Clean Architecture principles.

## Architecture

- **Product Service**: Manages products (Django, port 8001)
- **Order Service**: Manages orders (Django, port 8002)
- **User Service**: Manages users (Django, port 8003)
- **Payment Service**: Handles payments (Django, port 8004)
- **Inventory Service**: Manages inventory (Django, port 8005)
- **Frontend**: Next.js app (port 3000)

## Setup

### Prerequisites
- Python 3.9+
- Node.js 13+
- Docker
- Kubernetes (for production)

### Local Development

1. **Backend Services**:
   - Navigate to each service directory (e.g., `services/product-service`)
   - Create venv: `python3 -m venv venv`
   - Activate: `source venv/bin/activate`
   - Install: `pip install -r requirements.txt`
   - Run: `python manage.py runserver`

2. **Frontend**:
   - `cd frontend`
   - `npm install`
   - `npm run dev`

### Docker

- `docker-compose up --build`

### Kubernetes

- Apply manifests: `kubectl apply -f k8s/`
- Install Istio: `istioctl install`
- Enable Istio injection: `kubectl label namespace default istio-injection=enabled`
- Access via Istio gateway or Kong API gateway

## Service Mesh

- Istio for traffic management, security, and observability
- Gateway and VirtualService configured for all services

## Monitoring

- Prometheus for metrics collection
- Grafana for visualization and dashboards

## Event-Driven Architecture

- Celery for asynchronous task processing
- RabbitMQ as message broker

## API Gateway

- Kong for API management and routing

## Next Steps

- Implement distributed tracing (Jaeger)
- Add service discovery (Consul)
- Implement circuit breakers and retries
- Add rate limiting and security policies
- Set up log aggregation (ELK stack)
- Implement CI/CD pipeline