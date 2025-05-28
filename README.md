# SmartContractAnalyser

A tool for analyzing smart contracts for vulnerabilities and potential exploits.

## Requirements

- Docker and Docker Compose

## Setup

1. Clone the repository
   ```
   git clone <repository-url>
   cd SmartContractAnalyser
   ```

2. Create a `.env` file in the project root with the following content:
   ```
   # OpenAI API Key
   OPENAI_API_KEY=your_openai_api_key_here

   # Database Configuration
   POSTGRES_USER=user
   POSTGRES_PASSWORD=password
   POSTGRES_DB=mydb
   DATABASE_URL=postgresql://user:password@db:5432/mydb

   # Frontend Configuration
   REACT_APP_API_URL=http://localhost:4455
   ```

3. Make the start script executable:
   ```
   chmod +x start.sh
   ```

4. Run the application using the start script:
   ```
   ./start.sh
   ```

## Services

- **Frontend**: http://localhost:4456
  - React application for interacting with the smart contract analyzer

- **Backend API**: http://localhost:4455
  - Flask API for analyzing smart contracts
  - Endpoints:
    - `/register` - Register a new user
    - `/login` - Login and get an access token
    - `/analyze` - Analyze a smart contract
    - `/history` - Get analysis history
    - `/report/<wallet>/<filename>` - Get a specific analysis report

- **pgAdmin**: http://localhost:4457
  - Database management tool
  - Login: admin@admin.com / admin
  - To connect to the database:
    1. Add a new server
    2. Name: mydb
    3. Connection tab:
       - Host: db
       - Port: 5432
       - Database: mydb
       - Username: user
       - Password: password

## Usage

1. Open the frontend in your browser: http://localhost:4456
2. Register a new account or login with an existing account
3. Upload a Solidity smart contract file or paste the code directly
4. Click "Analyze" to analyze the contract for vulnerabilities
5. View the analysis results and download the report

## Troubleshooting

- If you encounter any issues, check the logs:
  ```
  docker-compose logs
  ```

- To check logs for a specific service:
  ```
  docker-compose logs [backend|frontend|db|pgadmin]
  ```

- To restart the services:
  ```
  docker-compose down
  docker-compose up -d
  ```

## Development

- Backend code is in the `backend` directory
- Frontend code is in the `react-client` directory
- Database models are in `backend/models.py`
- Smart contract analysis logic is in `backend/rlhf_agent/agent.py`
