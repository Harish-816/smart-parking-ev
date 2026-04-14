# Start from an Ubuntu base
FROM ubuntu:22.04

# Avoid timezone prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and NodeJS
RUN apt-get update && apt-get install -y python3 python3-pip curl python3-venv
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g pm2

# Copy all project files into the Docker container
WORKDIR /app
COPY . /app

# Install Python project dependencies securely in a virtual environment
RUN python3 -m venv .venv
RUN .venv/bin/pip install -r requirements.txt

# Install React project dependencies
RUN cd dashboard && npm install

# Build the React frontend for production (optional, if you serve it statically)
RUN cd dashboard && npm run build

# Expose the API port (Flask now serves the React frontend too!)
EXPOSE 5000

# Tell Docker to use PM2 to start all 9 applications, and keep docker alive
CMD ["pm2-runtime", "start", "ecosystem.config.js"]
