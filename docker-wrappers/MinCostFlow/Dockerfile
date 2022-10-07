#uses ubuntu as the base
FROM python:3.10.7

WORKDIR /MinCostFlow

RUN wget https://raw.githubusercontent.com/gitter-lab/min-cost-flow/main/minCostFlow.py

RUN pip install ortools
#==9.3.10497 don't need this any more because of min cost flow update