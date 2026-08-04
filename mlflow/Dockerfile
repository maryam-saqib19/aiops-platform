FROM python:3.10-slim

RUN pip install mlflow

WORKDIR /mlflow

RUN mkdir -p /mlflow/artifacts

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--workers", "1", "--backend-store-uri", "sqlite:///mlflow.db", "--artifacts-destination", "/mlflow/artifacts", "--allowed-hosts", "*"]
