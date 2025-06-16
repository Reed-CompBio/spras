FROM python:2.7.18

RUN pip install numpy==1.16.6
# Since this is an arbitrary internet ZIP file, we use the web archive link instead.
# TODO: checksum?
RUN wget https://web.archive.org/web/20250616194746/http://dsd.cs.tufts.edu/capdsd/files//capDSD-src.zip

RUN unzip capDSD-src.zip -d capDSD/
