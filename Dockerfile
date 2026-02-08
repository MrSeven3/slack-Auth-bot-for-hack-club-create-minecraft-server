FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 4348

CMD [ "python", "-m", "flask", "run", "-p", "4348","--host=0.0.0.0"]