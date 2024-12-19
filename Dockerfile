FROM python:3.11-bookworm

# ENV DEBUG=0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive 

VOLUME /data

RUN apt update

WORKDIR /app
RUN mkdir -p /app && cd /app

# Install Django dependencies
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt pip install -r requirements.txt

# Install cv2 dependencies
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Copy entirine Django project
COPY ./gradykrueger ./gradykrueger
COPY manage.py .

EXPOSE 8080

CMD ["python", "manage.py", "runserver", "--noreload", "--insecure", "--no-color", "0.0.0.0:8080"]
