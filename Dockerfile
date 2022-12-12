FROM python:3.9

RUN pip install --upgrade pip

# RUN pip3 install uwsgi==2.0.17
RUN pip3 install uwsgi
RUN pip3 install cython

RUN pip3 install -v --no-cache-dir --no-binary :all: falcon
# RUN pip3 install gevent==1.2.2
RUN pip3 install gevent

COPY app.py /code/app.py
COPY data/ /code/data/
COPY requirements.txt /code/requirements.txt

WORKDIR /code

RUN pip3 install -r requirements.txt
RUN pip3 install spacy
RUN python3 -m spacy download en_core_web_sm

CMD uwsgi --http 0.0.0.0:80 --wsgi-file  app.py --callable api --gevent 500 -l 128 -p 4 -L
# CMD uwsgi --http 0.0.0.0:80 --wsgi-file  app.py --callable api --gevent 500 --socket-timeout 120 -l 128 -p 4 -L
