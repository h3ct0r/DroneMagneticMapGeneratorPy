FROM ubuntu:bionic as base_dev_image
ENV DEBIAN_FRONTEND noninteractive

# APT packages
RUN apt-get update && apt-get install --no-install-recommends -y \
    nano \
    git \
    ssh \
    ca-certificates \
    python \
    python-pip \
    python-pyqt5 \
    python-pyqt5.qtwebkit \
    python-tk \
    build-essential && \
    rm -rf /var/lib/lists/*

RUN pip install --upgrade pip
RUN pip install --ignore-installed shapely numpy scipy matplotlib pillow
RUN pip install --ignore-installed pygame networkx

# Build code
COPY ./ /app/