# Base image: Node.js 18 with Alpine Linux (lightweight)
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN mkdir -p public/img src/img
RUN cp img/logo.png public/img/
RUN cp img/logo.png src/img/
ENV NODE_OPTIONS=--openssl-legacy-provider
RUN npm run build
RUN npm install -g serve
EXPOSE 3000
# CMD ["serve", "-s", "build", "-l", "80"]
CMD ["npm", "run", "start"]
