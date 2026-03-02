FROM node:20-slim

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the Vite dev port
EXPOSE 5173

# Run Vite in host mode to allow Docker mapping
CMD ["npm", "run", "dev", "--", "--host"]
