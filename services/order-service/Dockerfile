FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN sed -i 's/\r$//' entrypoint.sh

RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]