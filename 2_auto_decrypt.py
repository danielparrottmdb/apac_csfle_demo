from pymongo import MongoClient
from pymongo.encryption_options import AutoEncryptionOpts
from pymongo.encryption import ClientEncryption
import base64
import os
from bson.codec_options import CodecOptions
from bson.binary import STANDARD, UUID
import pprint
from your_credentials import get_credentials

credentials = get_credentials()

# start-key-vault
key_vault_namespace = "encryption.__keyVault"
# end-key-vault

connection_string = credentials["MONGODB_URI"]

# start-kmsproviders
path = "./master-key.txt"
with open(path, "rb") as f:
    local_master_key = f.read()
kms_providers = {
    "local": {
        "key": local_master_key  # local_master_key variable from the previous step
    },
}
# end-kmsproviders

# start-schema
# Make All fields random to use json pointer to reference key-id
json_schema = {}

patient_schema = {"medicalRecords.patients": json_schema}
# end-schema


# start-extra-options
extra_options = {"crypt_shared_lib_path": credentials["SHARED_LIB_PATH"]}
# end-extra-options

# start-client
fle_opts = AutoEncryptionOpts(
    kms_providers, key_vault_namespace, schema_map=patient_schema, **extra_options
)
secureClient = MongoClient(connection_string, auto_encryption_opts=fle_opts)
# end-client


# end-insert
regularClient = MongoClient(connection_string)
# start-find
print("Finding a document with regular (non-encrypted) client.")
result = regularClient.medicalRecords.patients.find_one({"name": "JiM Doe"})
pprint.pprint(result)

print("Finding a document with encrypted client, searching on an encrypted field")
pprint.pprint(secureClient.medicalRecords.patients.find_one({"name": "JiM Doe"}))
# end-find
