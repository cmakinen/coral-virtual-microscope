# coral-vm


## Running locally
Python, Pip, and Git are required for this application to function and will need to be installed locally. They are available for Windows, Linux and macOS platforms. 

Once the above pre-requisites are installed, the repository will need to be cloned locally using the following command. 
 
`git clone  https://github.com/cmakinen/coral-vm.git`

The following command needs to be executed inside the locally cloned repository to install all the necessary libraries to run this application. 

`cd coral-vm`
`pip install -r requirements.txt`

Installing Docker Desktop will make setting up the database much easier. It can be downloaded from https://www.docker.com/products/docker-desktop. If it is preferred to not install Docker, PostgreSQL will have to be downloaded and installed on the development system manually.

With Docker, a database server can be spun-up using the following command. A password can be specified to protect it.

`docker run -p 5432:5432 -e POSTGRES_PASSWORD=mysecretpassword -d postgres`

There is a .env file in the repository that will need to be updated so that the password matches what was setup in the previous command. 

The database needs to be created and initialized with initial histoslide data which can be done by using a small initialization script included in the repository. The following two commands need to be run to get the database updated.

`dotenv run python manage.py db upgrade`
`dotenv run python crud.py`

The application can be run using dotenv which reads the .env file in the repository and makes the properties in them available to the application as environment variables. Running the following should have the application running locally on port 5000. It can be accessed by pointing the browser to http://localhost:5000


## Deployment on Heroku

Heroku (https://www.heroku.com/) is a Platform as a Solution (PaaS) cloud option for hosting this application. This application has been configured to be deployable on Heroku. Heroku has multiple pricing options but based on the intended usage, this tool can work using the free tier (https://www.heroku.com/pricing). The free tier will automatically sleep after a 30-minute period of inactivity and will come back up on the first request after that.

Deployment to Heroku needs no Linux experience as they have command line interfaces (CLI) for Linux, Windows and macOS (https://devcenter.heroku.com/articles/heroku-cli#download-and-install).

You can configure your application on Heroku such that, whenever a change is made to the application it will automatically deploy those changes to the running portal. You could also deploy using the Heroku CLI if preferred.

### Create a Github Account

Sign up for an account at https://github.com and login to the account.

### Fork the existing coral-vm Github repository

Go to https://github.com/cmakinen/coral-vm and click the ‘Fork’ button to fork the repository into your account.

### Create a Heroku account

Register by going to https://signup.heroku.com and login to the account. 

### Create a Heroku application

An application can be created either on the command line or on the Heroku portal after logging in. The following command needs to be run if it is preferred to create it on the command line.

`heroku create <application-name>`

Complete instructions on how to create and run a new python application on Heroku can be found at https://devcenter.heroku.com/articles/getting-started-with-python?singlepage=true. 

### Connect the application to the Github repository

Use the instructions at https://devcenter.heroku.com/articles/github-integration to connect it to the Github repository created.


### Add a Heroku database addon

Creating and attaching a database to an application can be done on the Heroku portal or using the Heroku CLI. Instructions can be found at https://devcenter.heroku.com/articles/heroku-postgresql.

### Initialize the database

The database is initially empty and will need to be initialized. It can be initialized using the following command.

`heroku run python manage.py db upgrade`

The above should create the database but the database will be empty. The tables can be initialized with initial histoslide data using the following command.

`heroku run python crud.py `

Set histoslide remote URL path as environment variable

The following command lets the application running on Heroku know where to find the DZI histoslide images.

`heroku config:set SLIDE_BASE_URL=<dziimage_url>`

Any changes to the application on Github will be now be automatically deployed or it can be manually deployed from the Heroku portal. Instructions on deploying it can be found at https://devcenter.heroku.com/articles/github-integration.

