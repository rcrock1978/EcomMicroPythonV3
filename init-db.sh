#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until psql -U postgres -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing commands"

# Create databases
psql -U postgres -c "CREATE DATABASE IF NOT EXISTS product_db;"
psql -U postgres -c "CREATE DATABASE IF NOT EXISTS order_db;"
psql -U postgres -c "CREATE DATABASE IF NOT EXISTS user_db;"
psql -U postgres -c "CREATE DATABASE IF NOT EXISTS payment_db;"
psql -U postgres -c "CREATE DATABASE IF NOT EXISTS inventory_db;"

echo "Databases created successfully"