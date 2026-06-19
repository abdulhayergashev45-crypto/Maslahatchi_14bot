FROM python:3.11-slim

WORKDIR /code

# Kutubxonalarni o'rnatish
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Barcha fayllarni konteynerga ko'chirish
COPY . .

# Agar faylingiz nomi 'main.py' bo'lsa, pastdagi qator shunday bo'lishi kerak:
CMD ["python", "main.py"]
