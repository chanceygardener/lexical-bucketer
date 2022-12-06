#!/bin/zsh

for arg in "$@"
do
	case $arg in
		-b|--build)
		BUILD=1
		shift
		;;
		*)
		echo "Unrecognized argument: $1"
		shift
		;;
	esac
done
# load .env
source .env;
if [ $BUILD  ]
then
	echo "Building semantic bucketer at $PWD";
	if docker build -t bucketer_service --no-cache  --build-arg SPACY_MODEL=$SPACY_MODEL . ; then
		echo "Build succeeded, running bucketer_service container";
		
	else
		echo "Image build failed";
	fi
fi

docker run -p 8080:8080 -it bucketer_service;
