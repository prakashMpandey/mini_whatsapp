FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

# mysqlclient requires build tools and MySQL client development headers.
RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev pkg-config \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
