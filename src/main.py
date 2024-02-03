import argparse
import os
import sys
import pathlib

from anki.collection import Collection
import selenium
from seleniumwire import webdriver

from handlers import naver_tts


def parse_args():
    parser = argparse.ArgumentParser(description="Retrieve sound files for all korean words in given anki2 collection")

    parser.add_argument('collection', type=str,
                        help="The collection file to do the operation for")

    parser.add_argument('download_location', type=str,
                        help="The location to download temporary files")

    parser.add_argument("--src_field", action='store',  default='Korean',
                        type=str,
                        help="Name of the field to get the word from")

    parser.add_argument("--dst_field", action='store',  default='Sound',
                        type=str,
                        help="Name of the field to write the filename to")

    parser.add_argument("--query", action='store',  default='', type=str,
                        help="Filter which cards are downloaded for e.g 'deck:Korean'")

    parser.add_argument("--separator", action='store',  default='/',
                        type=str,
                        help="Used when dst contains more than one possible word")

    parser.add_argument("--driver", type=pathlib.Path, action='store',
                        required=False, default=None)

    parser.add_argument("--debug",  action='store_true', default=False,
                        required=False)

    parser.add_argument("--overwrite",  action='store_true', default=False,
                        required=False)

    parser.add_argument("--browser", action='store',
                        choices=['firefox', 'chrome'],
                        default='firefox', type=str)

    args = parser.parse_args()
    return args


def create_browser(args):

    if args.driver is None:
        raise Exception("Require driver path to run browser test. See --driver")
    if args.browser not in ["firefox", "chrome"]:
        raise Exception(f"Unsupported browser: {args.browser}")

    if args.browser == "firefox":
        options = webdriver.FirefoxOptions()
        service = selenium.webdriver.firefox.service.Service(args.driver)
        browser_class = webdriver.Firefox
    elif args.browser == "chrome":
        options = webdriver.ChromeOptions()
        service = selenium.webdriver.chrome.service.Service(args.driver)
        browser_class = webdriver.Chrome

    if args.debug:
        options.headless = False
    else:
        options.headless = True
    # TODO: Your Firefox profile cannot be loaded. It may be missing or inaccessible.
    browser = browser_class(service=service, options=options)
    browser.implicitly_wait(15)
    browser.set_page_load_timeout(15)
    return browser


def create_handlers(args, browser):
    return [naver_tts.NaverTTS(os.path.abspath(args.download_location),
                               browser)]


config = {
    "query": "",            # All cards
    "src_field": "Korean",  # Use field to get words
    "dst_field": "Sound",   # Put filename in this field
}


def run_through_collection(collection, handlers):
    # Lets make this a bit more readable
    query = config["query"]
    src_field = config["src_field"]
    dst_field = config["dst_field"]
    word_sep = config["separator"]

    for note_id in collection.find_notes(query):
        note = collection.getNote(note_id)

        keys = note.keys()

        if src_field not in keys:
            print(f"Missing src_field '{src_field}' for note " + note_id)
            continue
        if dst_field not in keys:
            print(f"Missing dst_field '{dst_field}' for note " + note_id)
            continue
        if note[dst_field] != "":  # Do not overwrite
            print(f"Skipping note {note_id} because '{src_field}' '{note[src_field]}' already has '{dst_field}' '{note[dst_field]}'")
            continue

        word = note[src_field]
        if word_sep in word:
            word = word.split(word_sep)[-1]

        if word is None or word == "":
            print(f"Was unable to find note {note_id}'s src word...")
            continue

        for retriever in handlers:
            filepath = retriever.query(word)
            if os.path.isfile(filepath):
                filename = collection.media.add_file(filepath)

                dst_value = f"[sound:{filename}]"
                note[dst_field] = dst_value

                ret = collection.update_note(note)
                print(f"Updated note {note_id} with '{src_field}' '{note[src_field]}' with '{dst_field}' '{note[dst_field]}': ret {ret}")
                collection.save()
                break


def main():

    args = parse_args()
    config.update(vars(args))

    collection_path = os.path.abspath(args.collection)
    download_directory = os.path.abspath(args.download_location)
    if not os.path.isfile(collection_path):
        print("The collection path given is invalid (must be file): " + collection_path)
        return 1
    if not os.path.isdir(download_directory):
        print("The download directory given does not exist: " + download_directory)
        return 1

    browser = create_browser(args)
    handlers = create_handlers(args, browser)

    collection = Collection(collection_path)

    try:
        run_through_collection(collection, handlers)
    except Exception as e:
        print(f"Something went wrong: {e}", file=sys.stderr)

    collection.media.check()
    collection.media.close()
    collection.close()
    browser.quit()


if __name__ == "__main__":
    handler = naver_tts.NaverTTS(None, None)
    handler.query_requests("날씨")
                       
