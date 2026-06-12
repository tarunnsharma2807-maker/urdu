FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the React app
RUN npm run build

# Expose port
EXPOSE 3000

# Use serve to run the application
CMD ["npm", "start"]
