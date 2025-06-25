# Create a Docker image for the Local Neighborhood algorithm here

FROM python:3.9-slim

# Set the working directory inside the container.
# This is where your local_neighborhood.py script and any inputs will be placed.

WORKDIR /app/LocalNeighborhood

# Copy the local_neighborhood.py script into the container.
# This path assumes your Dockerfile is in 'spras/docker-wrappers/LocalNeighborhood'
# and 'local_neighborhood.py' is in the root of your 'spras' clone.

COPY local_neighborhood.py .
