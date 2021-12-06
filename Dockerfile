FROM continuumio/miniconda3:latest

RUN apt-get update -y; apt-get upgrade -y; apt-get install -y default-libmysqlclient-dev python-dev gcc

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY environment.yml.bak environment.yml

RUN conda update -n base -c defaults conda
RUN conda env create -f environment.yml
RUN echo "alias l='ls -lah'" >> ~/.bashrc
RUN echo "source activate njbuswatcher" >> ~/.bashrc

# Setting these environmental variables is the functional equivalent of running 'source activate my-conda-env'
ENV CONDA_EXE /opt/conda/bin/conda
ENV CONDA_PREFIX /opt/conda/envs/njbuswatcher
ENV CONDA_PYTHON_EXE /opt/conda/bin/python
ENV CONDA_PROMPT_MODIFIER (njbuswatcher)
ENV CONDA_DEFAULT_ENV njbuswatcher
ENV PATH /opt/conda/envs/njbuswatcher/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV PYTHON_ENV="production"

# copy repo
WORKDIR /app
COPY . .
