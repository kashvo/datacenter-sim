FROM python:3.11-slim

WORKDIR /code

COPY locust/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY locustfile.py loadshapes.py ./
COPY profiles ./profiles

EXPOSE 8089
EXPOSE 5557
EXPOSE 5558

ENTRYPOINT ["locust", "-f", "locustfile.py,loadshapes.py"]
