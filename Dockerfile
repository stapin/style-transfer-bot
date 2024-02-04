FROM python:3

WORKDIR /usr/src/app

COPY . .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu118

ENV TG_BOT_TOKEN=<YOUR_TG_BOT_TOKEN_HERE>

CMD [ "python", "app.py" ]