# Maximum Edge Orientation wrapper
# https://github.com/agitter/meo/
FROM amazoncorretto:8-alpine3.19

RUN apk add --no-cache git

# Following https://lpsolve.sourceforge.net/5.5/Java/README.html, we configure lpsolve
RUN wget https://downloads.sourceforge.net/project/lpsolve/lpsolve/5.5.2.9/lp_solve_5.5.2.9_dev_ux64.tar.gz && \
    tar -xvzf lp_solve_5.5.2.9_dev_ux64.tar.gz && \
    wget https://downloads.sourceforge.net/project/lpsolve/lpsolve/5.5.2.9/lp_solve_5.5.2.9_java.zip && \
    unzip lp_solve_5.5.2.9_java.zip && \
    cp lp_solve_5.5_java/lib/ux64/liblpsolve55j.so . && \
    ldconfig . && \
    # and grab the jar
    cp lp_solve_5.5_java/lib/lpsolve55j.jar .

RUN git clone https://github.com/agitter/meo && \
    cd meo && \
    git reset --hard 1fe57e8ff3952c494e2b14dfdc563a84596e2fcd && \
    mkdir build && \
    javac -classpath ../lpsolve55j.jar:src -d ./build src/alg/EOMain.java && \
    jar -cvfe EOMain.jar EOMain src/alg/
