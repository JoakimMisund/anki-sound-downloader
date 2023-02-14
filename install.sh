wget https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux64.tar.gz
tar -zxvf geckodriver-v0.31.0-linux64.tar.gz
mv geckodriver ./bin
rm geckodriver-v0.31.0-linux64.tar.gz


wget https://chromedriver.storage.googleapis.com/108.0.5359.71/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver ./bin
rm chromedriver_linux64.zip

pip3 install -r requirements.txt
