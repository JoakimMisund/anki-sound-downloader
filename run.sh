SCRIPT_LOC="$(dirname -- "${BASH_SOURCE[0]}")"
SOUND_DIR="${SCRIPT_LOC}/sounds"
COLLECTION_PATH=$1

if [ ! -d ${SOUND_DIR} ]; then
    mkdir ${SOUND_DIR}
fi

if [ ! -f "${COLLECTION_PATH}" ]; then
    echo "Could not find anki collection ${COLLECTION_PATH}!"
    exit 1
fi

python3 ${SCRIPT_LOC}/src/main.py ${COLLECTION_PATH} ${SOUND_DIR} \
	--src_field Korean --dst_field Sound \
	--browser firefox --driver ${SCRIPT_LOC}/bin/geckodriver
