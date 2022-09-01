FROM python:3.9
# Server Config
ENV SERVER_PORT 8000
ENV SERVER_STORAGE /test
# Database Config
ENV DB_TYPE sqlite
ENV DB_HOST 127.0.0.1
ENV DB_PORT 3306
ENV DB_DATABASE cloudmodular
ENV DB_USER user
ENV DB_PASSWD 1234
# Admin Config
ENV ADMIN_EMAIL example@gmail.com
ENV ADMIN_PASSWD 1234
# JWT Config
ENV JWT_KEY jwt_key
ENV JWT_ALGORITHM HS256
# Authtication Config
ENV DATA_SHARED_LENGTH=7
ENV REACT_APP_TOKEN_EXPIRED=7
ENV MAX_UPLOAD_LEN=1000
# Update
RUN apt update -y
RUN apt upgrade -y
# install
RUN apt install -y sudo gcc make
RUN apt install -y python3-dev python3-pip
RUN apt install -y libffi-dev
RUN apt install -y build-essential
RUN apt install -y default-libmysqlclient-dev
RUN apt install -y git
# setting backend
WORKDIR /
RUN git clone -b release/v0.1.2 https://github.com/SweetCase-Cobalto/cloudmodular.git
WORKDIR /cloudmodular
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# setting frontend
RUN curl -sL https://deb.nodesource.com/setup_16.x | sudo -E bash -
RUN apt-get install -y nodejs
WORKDIR /
RUN git clone -b release/v0.1.2 https://github.com/SweetCase-Cobalto/cloudmodular-web.git
WORKDIR /cloudmodular-web
RUN npm i
RUN npm run build
# move frontend to backend
RUN mkdir /cloudmodular/web
RUN mv /cloudmodular-web/build/* /cloudmodular/web/
# run app
WORKDIR /cloudmodular
RUN chmod +x /cloudmodular/run.sh
ENTRYPOINT ["sh", "-c", "sh /cloudmodular/run.sh"]