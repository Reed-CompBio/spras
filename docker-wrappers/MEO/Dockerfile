# Maximum Edge Orientation wrapper
# https://github.com/agitter/meo/
FROM openjdk:8

WORKDIR /meo
RUN export MEO_TAG=v1.1.0 && \
    wget https://raw.githubusercontent.com/agitter/meo/$MEO_TAG/EOMain.jar

# Provide only the properties file as an argument to the jar file
ENTRYPOINT ["java", "-jar", "/meo/EOMain.jar"]
