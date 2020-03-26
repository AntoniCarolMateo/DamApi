# DAM-ProjectCore

## Description
This project create 3 services using docker and docker-compose.

- **Container 1**: MySQL Server. 
- **Container 2**: Adminer. Adminer (formerly PHPMyAdmin) is a full-featured database management tool written in PHP. Conversely to phpMyAdmin, it consists of a single file ready to deploy to the target server. Adminer is available for MySQL, MariaDB, PostgreSQL, SQLite, MS SQL, Oracle, Firebird, SimpleDB, Elasticsearch, and MongoDB.
- **Container 3**: Custom dockerfile based on Python3.7, where we create a folder to deploy the app, and every time we launch the container we reset and init the SQL Database and we start using gunicorn the Falcon API.

![DAMCORE](https://user-images.githubusercontent.com/61190134/75614085-4f4c0d80-5b35-11ea-9550-9f1d31de366b.png)

## Requirements

- docker
- docker-compose

## How to


```sh
$ cd docker
$ docker-compose up --build  [optional=(-d)]   #Start
$ docker-compose down                          #Stop
```

## Legend
- [A] Indicates that requires Authorization header (token)

## Resources

### Account Resources
- POST /account/create_token
- [A] POST /account/delete_token
- [A] GET /account/profile

### Users Resources
- POST /users/register
    - Required fields (body):
        - *String*: **username**: it must be a valid phone or a valid email.
        - *String*: **password**: it must be encrypted using sha256.
    

- [A] GET /users/show/{username:str}

