FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    procps \
    util-linux \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN find . -name "*.sh" -exec sed -i 's/\r$//' {} \;

RUN mkdir -p data

EXPOSE 5000

CMD ["python", "05_interface_web/webapp.py"]
