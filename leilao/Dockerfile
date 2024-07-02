# Use a imagem base do Cartesi com Python 3.10
FROM --platform=linux/riscv64 cartesi/python:3.10-slim-jammy

# Argumento para a versão do machine emulator tools
ARG MACHINE_EMULATOR_TOOLS_VERSION=0.14.1

# Baixar e instalar machine emulator tools
ADD https://github.com/cartesi/machine-emulator-tools/releases/download/v${MACHINE_EMULATOR_TOOLS_VERSION}/machine-emulator-tools-v${MACHINE_EMULATOR_TOOLS_VERSION}.deb /
RUN dpkg -i /machine-emulator-tools-v${MACHINE_EMULATOR_TOOLS_VERSION}.deb \
  && rm /machine-emulator-tools-v${MACHINE_EMULATOR_TOOLS_VERSION}.deb

# Labels para informações adicionais
LABEL io.cartesi.rollups.sdk_version=0.6.0
LABEL io.cartesi.rollups.ram_size=128Mi

# Definir variável de ambiente para o caminho do Cartesi
ENV PATH="/opt/cartesi/bin:${PATH}"

# Instalar dependências necessárias
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    busybox-static \
    jq \
    python3-pip \
  && rm -rf /var/lib/apt/lists/*

# Criar o usuário 'dapp' e definir o diretório de trabalho
RUN useradd -ms /bin/bash dapp
USER dapp
WORKDIR /home/dapp

# Copiar o arquivo requirements.txt e instalá-lo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do DApp
COPY dapp.py .

# Definir variável de ambiente para a URL do servidor rollup
ENV ROLLUP_HTTP_SERVER_URL="http://127.0.0.1:5004"

# Comando de entrada para inicializar o rollup
ENTRYPOINT ["rollup-init"]

# Argumento de comando para executar o script dapp.py
CMD ["python3", "dapp.py"]
