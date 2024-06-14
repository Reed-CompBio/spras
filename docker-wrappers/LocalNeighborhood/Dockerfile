# Create a Docker image for the Local Neighborhood algorithm here

# Local Neighborhood wrapper

FROM python:3.12.3-alpine3.20

WORKDIR /LocalNeighborhood

# Copy the py file to the working directory
COPY local_neighborhood.py .

# Copy the data subfolder to the working directory
COPY ln-network.txt .
COPY ln-nodes.txt .