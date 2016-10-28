#!/bin/bash

DICER_TOOL_PATH="$HOME/usr/share/dicer"

function usage() {
	echo "Usage: $0 IN_MODEL_PATH OUT_MODEL_PATH"
	echo ""
	echo "Transforms a deployment model (an *.xmi file) into an output TOSCA "
	echo "blueprint. The OUT_MODEL_PATH should be without an extension, "
	echo "because the tool will create three files: an .xmi, a .json and "
	echo "a .yaml. The .yaml file can be used in DICE deployment tool."
}

if [ "$#" != "2" ]
then
	usage

	exit 1
fi

JAR="$DICER_TOOL_PATH/dicer-core-0.1.0.jar"

if [ ! -e "$JAR" ]
then
	echo "DICER not installed."

	exit 2
fi

IN_MODEL="$(realpath $1)"
OUT_MODEL="$(realpath $2)"

cd "$DICER_TOOL_PATH"
java -jar "$JAR" -inModel "$IN_MODEL" -outModel "$OUT_MODEL"
