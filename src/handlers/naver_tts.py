import wget
import os
import sys

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

    def log(self, msg):
        print(msg)

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
