# Maximum Edge Orientation wrapper
# https://github.com/agitter/meo/
FROM openjdk:8
LABEL org.opencontainers.image.source https://github.com/Reed-CompBio/spras

WORKDIR /meo
RUN export MEO_TAG=v1.1.0 && \
    wget https://raw.githubusercontent.com/agitter/meo/$MEO_TAG/EOMain.jar

# Provide only the properties file as an argument to the jar file
# No longer set an ENTRYPOINT so that singularity exec can be used in addition to docker run
# ENTRYPOINT ["java", "-jar", "/meo/EOMain.jar"]

# Pass the entire command and properties file:
# java -jar /meo/EOMain.jar <properties_file>
