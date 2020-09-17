FROM       ubuntu:20.04
MAINTAINER Nikolay Bryskin

RUN apt-get update && apt-get -y upgrade && apt-get install -y curl wget software-properties-common gnupg2 && apt-get clean
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub \
    && apt-add-repository "deb http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/ /" \
    && add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -fy \
    python3.7-dev \
    python3-pip \
    python3-venv \
    cuda-libraries-10-0 \
    libnvidia-compute-418=418.67-0ubuntu1 \
    nvidia-compute-utils-418=418.67-0ubuntu1 \
    build-essential \
    git \
    git-lfs \
    libyaml-dev \
    vim \
    htop \
    nvtop \
    && apt-get clean

RUN curl -L https://storage.googleapis.com/gosu-common/libcudnn7_7.6.5.32-1%2Bcuda10.1_amd64.deb -O \
    && dpkg -i libcudnn7_7.6.5.32-1%2Bcuda10.1_amd64.deb

WORKDIR /app

ADD pyproject.toml poetry.lock ./
RUN pip3 install --pre poetry==1.1.0b1 poetry-core==1.0.0a9 && poetry config virtualenvs.in-project true
RUN poetry install --no-interaction

COPY . /app

CMD ["poetry", "run", "python", "server.py"]
