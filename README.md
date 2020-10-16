# text_api

## local development

To prepare your workspace for this application, first ensure you have pyenv and python installed. 
```
$ brew update && brew install pyenv
$ pyenv install --list  # to see available versions of Python
$ pyenv install 3.9.0
```

Next, ensure your version of python has virtualenv installed. 

```
$ pyenv global 3.9.0
$ pip install virtualenv
```

Next, create a local postgres database. If you have installed postgres client tools on your workstation, for instance by running `brew install postgres` on your Mac, you can enter `createdb text_api` into your terminal. 

```
$ brew install postgres # if needed
$ createdb text_api
```

Finally, create a local .env file in the root directory of this project to house necessary environment variable. It should look something like this:

```
DJANGO_SETTINGS_MODULE=text_api.settings
DB_NAME=text_api
DB_USERNAME=''
DB_PASSWORD=''
DB_HOST=localhost
DB_PORT=5432
LB_STRAT=weighted_random
SERVERS=https://jo3kcwlvke.execute-api.us-west-2.amazonaws.com/dev/provider1|0.3,https://jo3kcwlvke.execute-api.us-west-2.amazonaws.com/dev/provider2|0.7
CALLBACK_URL=http://ff38d78ff300.ngrok.io/ingest/
```

Now, you should be ready to initially populate your database. 

```
$ make seed
```

## testing

You can run the full test suite via the make command, `make test`.

## development shell

You can run a development shell with the application loaded by running `make shell`.

## development server

To start the application locally, run `make run`. 

## callback testing

To test the callback functionality, install the ngrok binary. Open a tunnel to port 8000 on your local machine with the following command:

```
$ /path/to/ngrok http 8000
```

Then, open up `text_api/settings.py` in a text editor or IDE of your choice. Add the ngrok provided public URL to the ALLOWED_HOSTS constant specified on line 32. 

Next, start you development server in a separate tab, as described above. Now your application should be ready to handle requests. 


