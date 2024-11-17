#!/bin/bash
set -euo pipefail

RESOURCE_GROUP_NAME=$1
CONTAINER_APP_ENVIRONMENT_NAME=$2
CERTIFICATE_NAME=$3

az containerapp env certificate create -g $RESOURCE_GROUP_NAME --name $CONTAINER_APP_ENVIRONMENT_NAME --certificate-name $CERTIFICATE_NAME --hostname $CERTIFICATE_NAME --validation-method CNAME
sleep 5
OUTPUT=$(az containerapp env certificate list -g $RESOURCE_GROUP_NAME --name $CONTAINER_APP_ENVIRONMENT_NAME --certificate $CERTIFICATE_NAME)

CERTIFICATE_PROVISIONING_STATUS=$(echo $OUTPUT | jq -r '.[].properties.provisioningState')
echo "Certificate provisioning status: $CERTIFICATE_PROVISIONING_STATUS"

while [ "$CERTIFICATE_PROVISIONING_STATUS" == "Pending" ]; do
    sleep 5
    echo "Waiting for certificate provisioning to complete..."
    OUTPUT=$(az containerapp env certificate list -g $RESOURCE_GROUP_NAME --name $CONTAINER_APP_ENVIRONMENT_NAME --certificate $CERTIFICATE_NAME)
    CERTIFICATE_PROVISIONING_STATUS=$(echo $OUTPUT | jq -r '.[].properties.provisioningState')
done

if [ "$CERTIFICATE_PROVISIONING_STATUS" == "Succeeded" ]; then
    echo "Certificate provisioning succeeded."
else
    echo "Certificate provisioning failed with status: $CERTIFICATE_PROVISIONING_STATUS"
    exit 1
fi