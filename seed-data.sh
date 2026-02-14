#!/bin/bash
set -e

echo "Waiting for services to be ready..."

# Wait for product service
until curl -f http://product-service:8000/api/products/ > /dev/null 2>&1; do
  echo "Waiting for product service..."
  sleep 5
done

# Wait for user service
until curl -f http://user-service:8000/api/users/ > /dev/null 2>&1; do
  echo "Waiting for user service..."
  sleep 5
done

# Wait for inventory service
until curl -f http://inventory-service:8000/api/inventory/ > /dev/null 2>&1; do
  echo "Waiting for inventory service..."
  sleep 5
done

echo "All services are ready. Starting seeding..."

# Seed products
echo "Seeding products..."
docker-compose exec -T product-service python manage.py seed_products --count=1000

# Seed users
echo "Seeding users..."
docker-compose exec -T user-service python manage.py seed_users --count=1000

# Seed inventory
echo "Seeding inventory..."
docker-compose exec -T inventory-service python manage.py seed_inventory --count=1000

echo "Seeding completed successfully!"