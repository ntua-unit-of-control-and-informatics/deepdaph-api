FROM python:3.8.2

RUN pip install --upgrade pip

RUN pip install flask
RUN pip install flask-restplus
RUN pip install Flask-OIDC
RUN pip install Pillow
RUN pip install numpy
RUN pip install requests
RUN pip install flask-cors
RUN pip install pyquots
RUN pip install pymongo
RUN pip install minio
RUN pip install Werkzeug==0.16.1

EXPOSE 8002



ADD help.py  /deepdaph-api/help.py
ADD models /deepdaph-api/models
ADD globals  /deepdaph-api/globals
ADD namespaces  /deepdaph-api/namespaces
ADD app.py /deepdaph-api/app.py
ADD conf /deepdaph-api/conf
ADD images /deepdaph-api/images

CMD ["python","/deepdaph-api/app.py"]
