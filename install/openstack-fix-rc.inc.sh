# Fix for broken rc files
if [[ -z "$OS_IDENTITY_API_VERSION" ]]
then
  if [[ -n "$OS_PROJECT_ID" ]] # v3
  then
    export OS_INTERFACE=public
    export OS_IDENTITY_API_VERSION=3
  else # v2
    export OS_ENDPOINT_TYPE=publicURL
    export OS_IDENTITY_API_VERSION=2
  fi
fi
