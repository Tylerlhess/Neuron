# copy to and run from ../ or C:\repos\Satori
# (updating process is the only thing that requires git)
# (vim for troubleshooting)

# python:slim will eventually fail, if we need to revert try this:
# FROM python:slim3.12.0b1-slim
FROM python:3.10-slim AS builder

## System dependencies
RUN apt-get update && \
    apt-get install -y build-essential wget git vim cmake zip curl && \
    mkdir /Satori && \
    cd /Satori && git clone https://github.com/SatoriNetwork/Synapse.git && \
    cd /Satori && git clone https://github.com/SatoriNetwork/Lib.git && \
    cd /Satori && git clone https://github.com/SatoriNetwork/Wallet.git && \
    cd /Satori && git clone https://github.com/SatoriNetwork/Engine.git && \
    cd /Satori && git clone https://github.com/SatoriNetwork/Neuron.git && \
    mkdir /Satori/Neuron/models && \
    mkdir /Satori/Neuron/models/huggingface && \
    chmod +x /Satori/Neuron/satorineuron/web/start.sh && \
    chmod +x /Satori/Neuron/satorineuron/web/start_from_image.sh && \
    dos2unix /Satori/Neuron/satorineuron/web/start.sh && dos2unix /Satori/Neuron/satorineuron/web/start_from_image.sh
    # NOTE: dos2unix line is used to convert line endings from Windows to Unix format

## Install everything
ENV HF_HOME=/Satori/Neuron/models/huggingface
ARG GPU_FLAG=off
ENV GPU_FLAG=${GPU_FLAG}
# for torch: cpu cu118 cu121 cu124 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --upgrade pip && \
    if [ "${GPU_FLAG}" = "on" ]; then \
    pip install --no-cache-dir torch==2.4.1 --index-url https://download.pytorch.org/whl/cu124; \
    else \
    pip install --no-cache-dir torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu; \
    fi && \
    pip install --no-cache-dir transformers==4.44.2 && \
    pip install --no-cache-dir /Satori/granite-tsfm && \
    pip install --no-cache-dir /Satori/chronos-forecasting && \
    cd /Satori/Wallet && pip install --no-cache-dir -r requirements.txt && python setup.py develop && \
    cd /Satori/Synapse && pip install --no-cache-dir -r requirements.txt && python setup.py develop && \
    cd /Satori/Lib && pip install --no-cache-dir -r requirements.txt && python setup.py develop && \
    cd /Satori/Engine && pip install --no-cache-dir -r requirements.txt && python setup.py develop && \
    cd /Satori/Neuron && pip install --no-cache-dir -r requirements.txt && python setup.py develop

## no need for ollama at this time.
#RUN apt-get install -y curl
#RUN mkdir /Satori/Neuron/chat
#RUN cd /Satori/Neuron/chat && curl -fsSL https://ollama.com/install.sh | sh
#RUN ollama serve
#RUN ollama pull llama3

# satori ui
EXPOSE 24601

WORKDIR /Satori/Neuron/satorineuron/web
CMD ["bash", "./start_from_image.sh"]

## RUN OPTIONS
# python -m satorisynapse.run async
# docker run --rm -it --name satorineuron -p 24601:24601 -v c:\repos\Satori\Neuron:/Satori/Neuron -v c:\repos\Satori\Synapse:/Satori/Synapse -v c:\repos\Satori\Lib:/Satori/Lib -v c:\repos\Satori\Wallet:/Satori/Wallet -v c:\repos\Satori\Engine:/Satori/Engine --env PREDICTOR=ttm --env ENV=prod satorinet/satorineuron:latest ./start.sh
# docker run --rm -it --name satorineuron -p 24601:24601 -v c:\repos\Satori\Neuron:/Satori/Neuron -v c:\repos\Satori\Synapse:/Satori/Synapse -v c:\repos\Satori\Lib:/Satori/Lib -v c:\repos\Satori\Wallet:/Satori/Wallet -v c:\repos\Satori\Engine:/Satori/Engine --env PREDICTOR=ttm --env ENV=prod satorinet/satorineuron:latest bash
# docker run --rm -it --name satorineuron -p 24601:24601 -v C:\Users\jorda\AppData\Roaming\Satori\Neuron:/Satori/Neuron -v C:\Users\jorda\AppData\Roaming\Satori\Synapse:/Satori/Synapse -v C:\Users\jorda\AppData\Roaming\Satori\Lib:/Satori/Lib -v C:\Users\jorda\AppData\Roaming\Satori\Wallet:/Satori/Wallet -v C:\Users\jorda\AppData\Roaming\Satori\Engine:/Satori/Engine --env ENV=prod satorinet/satorineuron:latest bash
# docker run --rm -it --name satorineuron satorinet/satorineuron:latest bash
# docker exec -it satorineuron bash

## BUILD PROCESS
# \Neuron> docker buildx prune --all
# \Neuron> docker builder prune --all
# \Neuron> docker buildx create --use
## dev version:
# \Neuron> docker buildx build --no-cache -f Dockerfile --platform linux/amd64             --build-arg GPU_FLAG=off --build-arg BRANCH_FLAG=dev  -t satorinet/satorineuron:test         --push .
## build both together (seems to fail some times):
# \Neuron> docker buildx build --no-cache -f Dockerfile --platform linux/amd64,linux/arm64 --build-arg GPU_FLAG=off --build-arg BRANCH_FLAG=main -t satorinet/satorineuron:test         --push .
## build separately:
# \Neuron> docker buildx build --no-cache -f Dockerfile --platform linux/amd64             --build-arg GPU_FLAG=off --build-arg BRANCH_FLAG=main -t satorinet/satorineuron:test         --push .
# \Neuron> docker buildx build --no-cache -f Dockerfile --platform linux/arm64             --build-arg GPU_FLAG=off --build-arg BRANCH_FLAG=main -t satorinet/satorineuron:rpi_satori   --push .
## build GPU version:
# \Neuron> docker buildx build --no-cache -f Dockerfile --platform linux/amd64             --build-arg GPU_FLAG=on  --build-arg BRANCH_FLAG=main -t satorinet/satorineuron:test-gpu     --push .
# \Neuron> docker pull satorinet/satorineuron:test
# \Neuron> docker run --rm -it --name satorineuron -p 24601:24601 --env ENV=prod                         satorinet/satorineuron:test bash
# \Neuron> docker run --rm -it --name satorineuron -p 24601:24601 --env ENV=prod --env PREDICTOR=xgboost satorinet/satorineuron:test bash
# \Neuron> docker tag satorinet/satorineuron:test satorinet/satorineuron:latest
# \Neuron> docker push satorinet/satorineuron:latest


# \Satori> docker buildx prune --all
# \Satori> docker builder prune --all
# \Satori> docker buildx create --use
# \Satori> docker buildx build --no-cache -f "Neuron/Dockerfile" --platform linux/amd64,linux/arm64 -t satorinet/satorineuron:test --push . ; docker pull satorinet/satorineuron:test
# \Satori> docker pull satorinet/satorineuron:test
# \Satori> docker run --rm -it --name satorineuron -p 24601:24601 --env ENV=prod satorinet/satorineuron:test bash
# \Satori> docker tag satorinet/satorineuron:test satorinet/satorineuron:latest
# \Satori> docker push satorinet/satorineuron:latest

# \Satori> docker buildx build --no-cache -f "Neuron/Dockerfile" --platform linux/amd64,linux/arm64 -t satorinet/satorineuron:test --push . ; docker pull satorinet/satorineuron:test ; docker tag satorinet/satorineuron:test satorinet/satorineuron:latest ; docker push satorinet/satorineuron:latest
