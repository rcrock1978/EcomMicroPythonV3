#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until psql -U postgres -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing commands"

# Create databases
psql -U postgres -c "CREATE DATABASE product_db;"
psql -U postgres -c "CREATE DATABASE order_db;"
psql -U postgres -c "CREATE DATABASE user_db;"
psql -U postgres -c "CREATE DATABASE payment_db;"
psql -U postgres -c "CREATE DATABASE inventory_db;"

echo "Databases created successfully"