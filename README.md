# Anki Sound Downloader (Korean)

This python script can download tts sounds for korean words in a anki collection
and add those sounds to the collection. 

# Install
Run `make` to download required drivers and install required python packages. It
has only been tested using the firefox geckodriver, but it should in theory work
with chromium aswell.

# Usage
Some gotchas:
- The source field should not start with a space because it can render the
  generated url useless
- If the destination field is not empty the script will skip the card.

Run `bash run.sh <Path to collection file>`. The collection file should be a
anki2 file.

## Card fields
The script allows for changing the destination and source field names. By
default it looks for words in *Korean*, and outputs a sound link in *Sound*.
An example is a card with the following fields where the second field is empty

1. Korean: 자격증
2. Sound:

After running the script it should update *Sound* to be *[sound:tts_자격증.mp3]*

1. Korean: 자격증
2. Sound: [sound:tts_자격증.mp3]

## Card template
Your card type need to have the following snippet of code.
```
{{#Sound}}
		{{Sound}}<br>
{{/Sound}}
```
