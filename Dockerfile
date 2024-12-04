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
    build-essential \
    libgeos-dev \
    python-setuptools \
    python-dev \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    freetype* \
    libpng-dev \
    libfreetype6-dev \
    pkg-config \
    libjpeg-dev \
    libsdl2-dev
    
RUN pip install --upgrade pip
RUN pip install --ignore-installed shapely 
RUN pip install --ignore-installed numpy 
RUN pip install --ignore-installed scipy 
RUN pip install --ignore-installed matplotlib 
RUN pip install --ignore-installed pillow
RUN pip install --ignore-installed networkx
# RUN pip install --ignore-installed pygame 

RUN rm -rf /var/lib/lists/*

# Build code
COPY ./ /app/
