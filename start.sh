#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Error: .env file not found. Please create a .env file with the required environment variables."
  echo "You can use the following template:"
  echo ""
  echo "# OpenAI API Key"
  echo "OPENAI_API_KEY=your_openai_api_key_here"
  echo ""
  echo "# Database Configuration"
  echo "POSTGRES_USER=user"
  echo "POSTGRES_PASSWORD=password"
  echo "POSTGRES_DB=mydb"
  echo "DATABASE_URL=postgresql://user:password@db:5432/mydb"
  echo ""
  echo "# Frontend Configuration"
  echo "REACT_APP_API_URL=http://localhost:4455"
  exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed. Please install Docker and try again."
  exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
  echo "Error: Docker Compose is not installed. Please install Docker Compose and try again."
  exit 1
fi

# Build and start the containers
echo "Building and starting the containers..."
docker-compose down
docker-compose up --build -d

# Wait for the containers to start
echo "Waiting for the containers to start..."
sleep 5

# Check if the containers are running
if [ "$(docker-compose ps -q | wc -l)" -ne 4 ]; then
  echo "Error: Not all containers are running. Please check the logs with 'docker-compose logs'."
  exit 1
fi

# Print success message
echo ""
echo "✅ All containers are running!"
echo ""
echo "🌐 Frontend: http://localhost:4456"
echo "🔌 Backend: http://localhost:4455"
echo "🗄️ pgAdmin: http://localhost:4457"
echo "   - Email: admin@admin.com"
echo "   - Password: admin"
echo ""
echo "📊 To connect to the database in pgAdmin:"
echo "   1. Add a new server"
echo "   2. Name: mydb"
echo "   3. Connection tab:"
echo "      - Host: db"
echo "      - Port: 5432"
echo "      - Database: mydb"
echo "      - Username: user"
echo "      - Password: password"
echo ""
echo "📝 To view the logs:"
echo "   - All containers: docker-compose logs"
echo "   - Specific container: docker-compose logs [backend|frontend|db|pgadmin]"
echo ""
echo "🛑 To stop the containers:"
echo "   docker-compose down"
echo ""