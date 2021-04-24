#!/bin/bash

set -e

function bold {
    echo -e "\e[1m${1}\e[0m"
}

function error {
    bold "ERROR: $1"
    exit 1
}

function error_envvar_not_set {
    # $1 missing variable
    # $2 optional reason
    error "environment variable not set: ${1}\n
           ${2}\n
           Please run the container passing the '-e ${1}=value' argument."
}

DAEMON="${DAEMON}"
VERSION="${VERSION}"
RS_ASN="${RS_ASN}"
ROUTER_ID="${ROUTER_ID}"
LOCAL_PREFIXES="${LOCAL_PREFIXES}"
IP_VER="${IP_VER}"

CLIENTS_FILE_PATH="/root/clients.txt"
OUTPUT_DIR="/root/arouteserver_configs"
OUTPUT_DIR_HTML="/root/arouteserver_html"

if [[ ! -e "${OUTPUT_DIR}" && ! -d "${OUTPUT_DIR}" ]]; then
    error "The output directory ${OUTPUT_DIR} can't be found.
          This is the directory where the configurations generate by ARouteServer will be saved.
          Please be sure to mount the desired directory of the host to the ${OUTPUT_DIR} directory on the container.
          You can run the container passing the '-v PATH_OF_DIRECTORY_ON_THE_HOST:${OUTPUT_DIR}' argument."
fi

if [[ -z "${DAEMON}" ]]; then
    error_envvar_not_set "DAEMON"
fi

if [[ -z "${VERSION}" ]]; then
    error_envvar_not_set "VERSION"
fi

if [[ ! -e "${CLIENTS_FILE_PATH}" ]]; then
    error "Couldn't find the file ${CLIENTS_FILE_PATH} on the container.\n
           Please mount the local file where the list of clients is defined using '-v PATH_OF_CLIENTS_FILE_ON_THE_HOST:${CLIENTS_FILE_PATH}:ro' argument."
fi

IP_VER_ARG=""
OUTPUT_FILE="${DAEMON}.cfg"

if [[ "${DAEMON}" == "bird" ]]; then
    set +e
    egrep "^1\." <<< "${VERSION}" &>/dev/null
    IP_VER_REQUIRED=$?  # 0 = IP_VER is required
    set -e

    if [[ ${IP_VER_REQUIRED} -eq 0 ]]; then
        if [[ -z "${IP_VER}" ]]; then
            error_envvar_not_set "IP_VER" "When BIRD 1.x is used, IP_VER must be set."
        else
            IP_VER_ARG="--ip-ver ${IP_VER}"
            OUTPUT_FILE="${DAEMON}${IP_VER}.cfg"
        fi
    fi
fi

if [[ ! -e /etc/arouteserver/general.yml ]]; then
    if [[ -z "${RS_ASN}" ]]; then
        error_envvar_not_set "RS_ASN"
    fi

    if [[ -z "${ROUTER_ID}" ]]; then
        error_envvar_not_set "ROUTER_ID"
    fi

    if [[ -z "${LOCAL_PREFIXES}" ]]; then
        error_envvar_not_set "LOCAL_PREFIXES"
    fi

    echo ""
    bold "Configuring ARouteServer for ${DAEMON} ${VERSION}..."
    echo ""

    arouteserver \
        configure --preset-answer \
            daemon=${DAEMON} \
            version=${VERSION} \
            asn=${RS_ASN} \
            router_id=${ROUTER_ID} \
            black_list=${LOCAL_PREFIXES}
else
    echo ""
    bold "The user-provided configuration from general.yml will be used."
    echo ""
fi

if [[ -e "${OUTPUT_DIR_HTML}" && -d "${OUTPUT_DIR_HTML}" ]]; then
    OUTPUT_FILE_HTML="${DAEMON}.html"

    echo ""
    echo "Generating HTML textual representation of route server's options and policies"
    echo ""

    OUTPUT_PATH_HTML="${OUTPUT_DIR_HTML}/${OUTPUT_FILE_HTML}"

    arouteserver \
        html \
        --clients "${CLIENTS_FILE_PATH}" \
        -o "${OUTPUT_PATH_HTML}"

    echo ""
    bold "Textual representation of route server policy for ${DAEMON} saved to ${OUTPUT_PATH_HTML} (path on the container)."
    echo "You will find the textual representation file in your host system, inside the directory that you mounted at run-time."
    echo ""
fi

echo ""
bold "Generating route server configuration for ${DAEMON} ${VERSION}..."
echo ""

OUTPUT_PATH="${OUTPUT_DIR}/${OUTPUT_FILE}"

arouteserver \
    "${DAEMON}" \
    --target-version "${VERSION}" \
    ${IP_VER_ARG} \
    --clients "${CLIENTS_FILE_PATH}" \
    -o "${OUTPUT_PATH}"

echo ""
bold "Route server configuration for ${DAEMON} ${VERSION} saved to ${OUTPUT_PATH} (path on the container)."
echo "You will find the configuration file in your host system, inside the directory that you mounted at run-time."
echo ""
