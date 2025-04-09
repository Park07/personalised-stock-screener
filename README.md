# SENG3011-Foxtrot

# Quick start instructions

## Backend

Comprehensive guide on how to quickly get started on our project

For the OS please either use vlab or WSL ubuntu. Not too sure if this will work on mac.

first create a new directory & create a new virtual python environment

```shell
python -m venv seng3011
```

then install talib 

cd into the site-packages directory inside your virtual environment
```
cd seng3011
cd lib
cd python3.10
cd site-packages
```

double check that C++ build tools are installed
```
apt-get update && apt-get install build-essential     
```

then install the ta-lib tarball 
```
wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz
tar -xzf ta-lib-0.6.4-src.tar.gz
cd ta-lib-0.6.4/
./configure --prefix=/usr
make
sudo make install
pip install TA-lib
```

then clone our git repository into the seng3011 directory then install all of our requirements
```
pip install -r requirement.txt
```

head to these websites and create api keys
```
https://site.financialmodelingprep.com/
https://alpaca.markets/
```

activate your venv and set them as env variables when you are inside the project directory

```
source bin/activate
export ALPACA_SECRET_KEY='apikeyhere'
export ALPACA_PUBLIC_KEY='apikeyhere'
export FMP_API_KEY='apikeyhere'
```

to finially run the program set the flask environment variable
make sure you are in the same directory as app.py
```
export FLASK_APP='app.py'
```

then do
```
flask run
```

## Frontend

here is how you would setup the front end.

cd into the 'frontend' directory
```
cd frontend
npm install vite
npm install tailwind
npm install apexcharts react-apexcharts
npm install react-icons 
npm run build 
```

Wait for it build and done

Note: our AWS RDS and AWS EC2 needs to be active in order for everything to work as we are hosting our database and backend remotely. 
