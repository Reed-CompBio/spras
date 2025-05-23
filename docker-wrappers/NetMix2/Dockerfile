FROM python:3.6.15-bullseye

RUN COMMIT_SHA_NETMIX2=110954e27ec1911b6fe68b6a34352fecca494922 && \
    wget https://github.com/raphael-group/netmix2/tarball/$COMMIT_SHA_NETMIX2 && \
    tar -zxvf $COMMIT_SHA_NETMIX2 && \
    rm $COMMIT_SHA_NETMIX2 && \
    mv raphael-group-netmix2-* NetMix2 && \
    cd NetMix2/ && \
    # and install locfdr!
    COMMIT_SHA_LOCFDR=5e2c073ee67373cc51c93b64b8441ce50e660bba && \ 
    wget https://github.com/leekgroup/locfdr-python/tarball/$COMMIT_SHA_LOCFDR && \
    tar -zxvf $COMMIT_SHA_LOCFDR && \
    rm $COMMIT_SHA_LOCFDR && \
    mv leekgroup-locfdr-python-* locfdr && \
    cd locfdr && \
    python setup.py install

COPY requirements.txt .

RUN pip install -r requirements.txt
