#Builds base python container from python image on docker hub
FROM python:3-alpine

# Specifies where to run the command that comes after it, in this case tells the copy command where to copy from
WORKDIR /LocalNeighborhood

#changed this line to copy the code from local system into the Docker container
COPY local_neighbor.py .

