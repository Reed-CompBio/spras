# DOMINO wrapper
# https://github.com/Shamir-Lab/DOMINO
FROM python:3.8.20-bullseye

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY *.patch .

RUN git clone https://github.com/Shamir-Lab/DOMINO/ && \
    cd /DOMINO && \
    git reset --hard 85dad1515717b425b17f58f92b13a063ccccb85d && \
    git config user.email "email@example.com" && \
    git config user.name "Non-existent User" && \
    # https://stackoverflow.com/a/4832785/7589775
    git apply --ignore-space-change --ignore-whitespace --verbose /*.patch
