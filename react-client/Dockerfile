# Base image: Node.js 18 with Alpine Linux (lightweight)
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./

# Install dependencies
# Using 'npm ci' for clean install based on package-lock.json
RUN npm ci

# Copy all application files to the container
COPY . .

# Set NODE_OPTIONS for OpenSSL compatibility
# This helps with older React applications that need legacy OpenSSL
ENV NODE_OPTIONS=--openssl-legacy-provider

# Build the React application
# This creates optimized production files in the /app/build directory
RUN npm run build

# Install a simple HTTP server to serve the static files
# serve is a lightweight server that can handle SPA routing
RUN npm install -g serve

# Expose port 80 (standard HTTP port)
# This matches the port expected in docker-compose.yml
EXPOSE 80

# Start the server
# -s flag serves the app as a single-page application (handles client-side routing)
# -l 80 sets the listening port to 80
CMD ["serve", "-s", "build", "-l", "80"]
