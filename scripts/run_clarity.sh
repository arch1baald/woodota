# Run script only from project root folder

CLARITY_FOLDER="$(pwd)/parser"
CLARITY_IMAGE=odota/parser
CLARITY_CONTAINER=parser

# Clone the code
if [[ ! -d "$CLARITY_FOLDER" ]];
then
    git clone https://github.com/arch1baald/clarity-parser.git "$CLARITY_FOLDER"
else
    echo 'Clarity Parser source code is located at:' "$CLARITY_FOLDER"
fi

# Build
if [[ "$(docker images -q $CLARITY_IMAGE)" == "" ]];
then
    if [[ $(uname -m) == "arm64" ]];
    then
        sudo docker build -t $CLARITY_IMAGE --platform linux/arm64/v8 parser/
    else
        sudo docker build -t $CLARITY_IMAGE --platform parser/
    fi
fi

# Run
if [[ "$(docker container inspect -f '{{.State.Running}}' $CLARITY_CONTAINER)" == "true" ]];
then
    echo 'Container ID:' $(docker ps -f name=$CLARITY_CONTAINER --format '{{.ID}}')
else
    sudo docker run -d --name $CLARITY_CONTAINER -p 5600:5600 $CLARITY_IMAGE
fi
