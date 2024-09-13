#!/bin/bash

CONTAINER_NAME="museum_postgres"
DB_NAME="museum_db"
DB_USER="user"
DB_PASSWORD="password"

# Check if the container already exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing PostgreSQL container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Start a new PostgreSQL container
echo "Starting new PostgreSQL container..."
docker run --name $CONTAINER_NAME \
    -e POSTGRES_DB=$DB_NAME \
    -e POSTGRES_USER=$DB_USER \
    -e POSTGRES_PASSWORD=$DB_PASSWORD \
    -p 5432:5432 \
    -d postgres:13

echo "PostgreSQL container is running."
echo "Connection details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"