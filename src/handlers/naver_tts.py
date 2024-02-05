import requests
import os
import sys
import hmac
import base64

import zlib
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


def wait_find(element, cond, timeout=15):
    WebDriverWait(element, timeout).until(expected_conditions.presence_of_element_located(cond))
    return element.find_element(*cond)


def wait_finds(element, cond, timeout=15):
    WebDriverWait(element, timeout).until(expected_conditions.presence_of_element_located(cond))
    return element.find_elements(*cond)


class NaverTTS:
    def __init__(self, dest_directory, browser):
        self._dest_directory = dest_directory
        self._browser = browser

        self._session = requests.Session()
        self._session.get("https://papago.naver.com/")

        self._uuid = "4bd9a1f7-5f83-4621-b05f-eba83e73e4cf"
        self._makeid_url = "https://papago.naver.com/apis/tts/makeID"
        self._key = "v1.8.0_33f494c37e"

    def log(self, msg):
        print(msg)

    def create_authorization(self, timestamp):
        message = self._uuid + "\n" + self._makeid_url + "\n" + timestamp
        mac = hmac.new(self._key.encode(), message.encode(), 'MD5')
        auth = base64.b64encode(mac.digest()).decode()
        return f"PPG {self._uuid}:{auth}"

    def query_requests(self, word, file_format="tts_{word}"):
        dest_filename = self._dest_directory + "/" + file_format.format(word=word) + ".mp3"
        if os.path.isfile(dest_filename):
            return dest_filename

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Accept": "application/json,image/avif,image/webp,*/*",
            "Accept-Language": "en",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://papago.naver.com/",
            "Origin": "https://papago.naver.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        self._session.headers.update(headers)


        response = self._session.get("https://papago.naver.com/apis/timestamp")
        timestamp = response.json()["timestamp"]
        timestamp = str(int(timestamp) + 60000)
        
        self._session.headers.update({
            "Authorization": self.create_authorization(timestamp),
            "Timestamp": timestamp,
        })
        
        data = {
            "alpha": "0",
            "pitch": "0",
            "speaker": "kyuri",
            "speed": "0",
            "text": word
        }

        response = self._session.post(self._makeid_url,
                                data=data)

        if response.status_code != 200:
            print(response)
            print(response.content)
            return None
        
        try:
            response_json = response.json()
            id_ = response_json["id"]

            headers = {
                "Accept": "audio/webm,audio/ogg,audio/wav,audio/*;q=0.9,application/ogg;q=0.7,video/*;q=0.6,*/*;q=0.5",
                "Accept-Encoding": "gzip, deflate, br, identity",
                "Sec-Fetch-Dest": "audio",
                "Sec-Fetch-Mode": "no-cors",
            }

            self._session.headers.update(headers)
            
            url = f"https://papago.naver.com/apis/tts/{id_}"
            response = self._session.get(url)
            
            with open(dest_filename, "wb") as f:
                f.write(response.content)

            self.log(f"File downloaded to {dest_filename}")
            if (os.path.getsize(dest_filename) == 0):
                raise Exception("Error downloading file " + url +
                                " to " + dest_filename, file=sys.stderr)

            return dest_filename
            
        except Exception as e:
            print(e)

        return None


    def query(self, word, file_format="tts_{word}"):
        dest_filename = self._dest_directory + "/" + file_format.format(word=word) + ".mp3"
        if os.path.isfile(dest_filename):
            return dest_filename

        # Open up the papago translator with the given word
        # Then click the button to initiate the tts request
        url = "https://papago.naver.com/?sk=ko&tk=en&st={word}".format(word=word)
        self.log("Opening {url} in browser".format(url=url))
        for attempt in range(5):
            try:
                self._browser.get(url)
                break
            except Exception as e:
                print(f"Failed to retrieve {url}, trying again")
                print(str(e))

        del self._browser.requests  # Clear before we click

        toolbar = wait_find(self._browser, (By.ID, "btn-toolbar-source"))
        button = wait_find(toolbar, (By.CLASS_NAME, "btn_sound___2H-0Z"))
        self.log("Page fully loaded. Clicking {button}".format(button=button))
        button.click()  # This call seems to be blocking/waiting

        self.log("Click completed".format())
        # Go through the requests made and find the one we should have
        # If there are more than one requests there is something wrong
        # that needs to be investigated
        possible_requests = [r for r in self._browser.requests if r.url == "https://papago.naver.com/apis/tts/makeID"]
        assert (len(possible_requests) == 1)
        request = possible_requests[0]
        if request.response.status_code != 200:
            raise Exception(f"Failed to retrieve sound for {word}! status: {request.response.status_code}")

        # Parse the body of the response appropriatly
        # The output of this block should be an id that is used to
        # finally download the sound
        response_text = request.response.body
        if request.response.headers['content-encoding'] == "gzip":
            # https://stackoverflow.com/questions/2695152/in-python-how-do-i-decode-gzip-encoding
            response_text = zlib.decompress(request.response.body,
                                            16+zlib.MAX_WBITS).decode("utf-8")
        else:
            raise Exception(f"unexpected encoding: {request.response.headers['content-encoding']}")

        if "json" not in request.response.headers['content-type']:
            raise Exception(f"unexpected content type: {request.response.headers['content-type']}")
        if "UTF-8" not in request.response.headers['content-type']:
            raise Exception(f"unexpected content type: {request.response.headers['content-type']}")
        response_json = json.loads(response_text)
        sound_id = response_json['id']
        self.log(f"Received a response to the request: {response_json}")

        # Armed with the id of the generated sound we can download
        # the sound bit using the following url
        url = "https://papago.naver.com/apis/tts/" + sound_id
        self.log("Opening {url} in browser".format(url=url))
        filename = wget.download(url, out=dest_filename, bar=None)

        self.log("File downloaded to {filename}".format(filename=filename))
        if (os.path.getsize(filename) == 0):
            print("Error downloading file " + request.url +
                  " to " + filename, file=sys.stderr)
            dest_filename = None

        return filename
