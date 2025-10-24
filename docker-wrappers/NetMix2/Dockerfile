FROM python:3.7.17-bullseye

RUN COMMIT_SHA_NETMIX2=110954e27ec1911b6fe68b6a34352fecca494922 && \
    wget https://github.com/raphael-group/netmix2/tarball/$COMMIT_SHA_NETMIX2 && \
    tar -zxvf $COMMIT_SHA_NETMIX2 && \
    rm $COMMIT_SHA_NETMIX2 && \
    mv raphael-group-netmix2-* NetMix2 && \
    cd NetMix2/ && \
    # and install locfdr!
    cd locfdrpython && \ 
    python3 setup.py install

COPY requirements.txt .

RUN pip install -r requirements.txt
