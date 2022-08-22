# CloudModular [Server]
<p align="center">
    <img width="70%" src="https://raw.githubusercontent.com/SweetCase-Cobalto/cloudmodular/main/readme-asset/title.png?token=GHSAT0AAAAAABUZRX43MQBPTOW7QM2WY5DWYVHIGLA">
</p>

<div align="center">
    <img src="https://img.shields.io/badge/Python 3.9-blue?style=flat-square&logo=python&logoColor=white" />
    <img src="https://img.shields.io/badge/fastapi-109989?style=flat-square&logo=FASTAPI&logoColor=white" />
    <img src="https://img.shields.io/badge/SQLite-07405E?style=flat-square&logo=sqlite&logoColor=white">
    <img src="https://img.shields.io/badge/MySQL-005C84?style=flat-square&logo=mysql&logoColor=white">
    <img src="https://img.shields.io/badge/MariaDB-003545?style=flat-square&logo=mariadb&logoColor=white">
    <img src="https://img.shields.io/badge/JWT-000000?style=flat-square&logo=JSON%20web%20tokens&logoColor=white">
    <img src="https://img.shields.io/badge/Docker-2CA5E0?style=flat-square&logo=docker&logoColor=white">
    <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white">
</div>
<div align="center">
<a href="https://codecov.io/gh/SweetCase-Cobalto/cloudmodular" > 
 <img src="https://codecov.io/gh/SweetCase-Cobalto/cloudmodular/branch/main/graph/badge.svg?token=D7L8SNPUKF"/>
</a>
<img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/Sweetcase-Cobalto/cloudmodular?style=flat-square">
</div>

The Constructive Cloud Service for your NAS Server

직접 설치하는 클라우드 서비스 (Server)

* * *

**개발 현황**

[![](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=notion&logoColor=white)](https://www.notion.so/CloudModular-ade21e9e1a324cfc916da7d051893717)

## 소개
* 원격 서버 및 NAS Server의 파일 관리 서비스를 지원하기 위해 개발된 설치형 저용량 파일 호스팅 서비스
* 타 서버로부터 금액을 지불하고 일정 용량을 할당 받는 것이 아닌, 개인 서버만 갖고 있으면 이 웹 어플리케이션을 이용해 파일 호스팅 서버를 운용할 수 있습니다.
* PROJECT Microcloudchip의 3번째 작품으로 버전은 2.0입니다.
* 해당 Repository는 Server Repository입니다. Endpoint Repository는 아래에서 확인하실 수 있습니다.
    * [Frontend Repo (Javascript/ReactJS/Redux)](https://github.com/SweetCase-Cobalto/cloudmodular-web)

## 기능
* 기본적인 파일/디렉토리를 관리합니다.
    * 생성/수정/삭제/다운로드
* 파일/디렉토리에 대한 전체 공유가 가능합니다.
    * 공유 기한 선택 가능
* 파일/디렉토리에 즐겨찾기를 통한 빠른 데이터 접근
* 다양한 검색 필터링
    * 연관 검색어
    * 즐겨찾기 및 공유 여부
    * 이름, 생성순 정렬
* 외부 리소스를 지원합니다.
    * 외부 스토리지를 지원.
        * 외부 스토리지를 연걸 함으로써 Docker의 용량 한계를 극복할 수 있습니다
        * 어플리케이션에 문제가 발생해도 스토리지를 직접 접근할 수 있습니다.
            > 단 스토리지에 있는 파일/디렉토리를 수정 또는 삭제 시 데이터 동기화에 문제가 생길 수 있습니다.
    * 외부 데이터베이스 지원
        * 마찬가지로 SQLite 뿐만 아니라 MySQL를 사용할 수 있습니다.
* 여러 사용자 관리
    * 하나의 관리자가 여러 사용자를 생성 및 관리할 수 있습니다.
    * 모든 사용자가 사용할 수 있는 최대 용량 크기는 해당 스토리지가 위치한 디스크 파티션 용량 중 남아있는 용량의 50%입니다. 따라서 과도한 사용으로 인한 다른 데이터 관리에 방해받지 않습니다.
* * *

## 설치 및 실행 방법(사용자 기준)
해당 어플리케이션은 Docker기반의 Container입니다. docker container 생성을 통해 어플리케이션을 한번에 설치 + 실행이 가능합니다.
### 공통
```bash
$ sudo docker run -it -d -p [포트]:[포트] \
    -v [외부 스토리지 루트]:[도커 내부 스토리지 루트] \
    -e SERVER_PORT=[포트] \
    -e SERVER_STORAGE=[도커 내부 스토리지 루트] \
    -e ADMIN_EMAIL=[관리자 이메일] \
    -e ADMIN_PASSWD=[관리자 비빌번호] \
    -e JWT_KEY=[jwt key] \
    -e JWT_ALGORITHM=HS256 \
    -e DATA_SHARED_LENGTH=[공유 기한] \
    ... DB 관련 ENV 추가 (아래 참고) ...
    --name [container name] ghcr.io/sweetcase-cobalto/cloudmodular:0.1.0
```
* ```SERVER_PORT```: 연결할 서버 포트 입니다.
* ```SERVER_STORAGE```: 데이터가 저장될 스토리지를 정합니다. 스토리지 위치는 항상 Docker 밖의 디렉토리와 동기화가 되어야 하기 때문에 앞에 ```-v```를 사용하여 외부 디렉토리 루트를 Docker 내부 루트로 마운트 합니다.
    ```
        예시
        -v /home/recoma/my_storage:/storage
    ```
* ```ADMIN_EMAIL```, ```ADMIN_PASSWD```: 관리자의 정보 입니다. 이 두개의 변수는 관라자 계정의 정보가 됩니다.
* ```JWT_KEY```: Jwt암호화를 위한 Key를 입력합니다. 어느 문자열이든 상관없습니다.
* ```JWT_ALGORITHM```: JWT Algorithm으로 HS256을 권장합니다.
* ```DATA_SAHRED_LENGTH```: 데이터를 공유할 때, 그 공유 기간 입니다. 단위를 "일" 입니다.

### SQLite를 사용하는 경우
```
$ sudo docker run -it -d -p [포트]:[포트]
    ...  생략 ...
    -e DB_TYPE=sqlite
    ... 생략 ...
```
### MySQL을 사용하는 경우
```
$ sudo docker run -it -d -p [포트]:[포트]
    ...  생략 ...
    -e DB_TYPE=mysql
    -e DB_PORT=[DB 포트]
    -e DB_HOST=[DB 호스트]
    -e DB_DATABASE=[데이터베이스 이름]
    -e DB_USER=[데이터베이스 유저 아이디]
    -e DB_PASSWD=[데이터베이스 유저 패스워드]
    ... 생략 ...
```

## 설치 및 실행 방법(개발자 기준)
해당 어플리케이션은 Unix 환경에서만 작동합니다. Windows를 사용할 경우, WSL2를 미리 설치해 주세요.
### Backend
0. 필수 요소들을 다운받습니다.
```bash
apt update -y
apt upgrade -y
apt install -y sudo gcc make
apt install -y python3-dev python3-pip
apt install -y libffi-dev
apt install -y build-essential
apt install -y default-libmysqlclient-dev
apt install -y git
```
1. 파이썬 가상 머신을 생성합니다. (3.9 이상)
2. repository를 다운받습니다.
3. server 디렉토리로 이동합니다.
4. 아래의 명령어로 패키지들을 설치합니다.
```
$ pip install -r requirments.txt
```
5. .env파일을 생성하고 아래와 같이 작성합니다. sqlite를 사용할 경우, DB_TYPE만 입력합니다.
```
SERVER_PORT=<서버가 돌아갈 포트>
SERVER_STORAGE=<서버에 돌아가는 데이터들을 저장할 때 사용>

DB_TYPE=<mysql/mariadb of sqlite>
# 아래 DB Config는 SQlite를 사용할 경우 필요 없음
DB_HOST=<DB Host>
DB_PORT=<DB Port>
DB_DATABASE=<DB Name>
DB_USER=<DB User ID>
DB_PASSWD=<DB User pswd>

ADMIN_EMAIL=<관리자 이메일>
ADMIN_PASSWD=<관리자 패스워드>

JWT_KEY=<jwt key>
JWT_ALGORITHM=<jwt 알고리즘 (HS256 권장)>

DATA_SHARED_LENGTH=<파일/디렉토리 공유 길이 (ex: 3 -> 3일)>
```
5. 테스트를 진행하고 싶은 경우, 아래와 같이 명령어를 입력합니다. (단 테스트를 진행할 때 DB나, 스토리지에 어느 데이터도 남아있어서는 안됩니다.)
```
$ pytest
```
6. 테스트가 아닌 어플리케이션 자체를 실행하고 싶은 경우, Migration을 진행한 뒤 실행합니다.
```
$ python main.py --method=migrate --type=dev
$ python main.py --method=run-app --type=dev
```