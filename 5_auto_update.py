from pymongo import MongoClient
from pymongo.encryption_options import AutoEncryptionOpts
import pprint
from your_credentials import get_credentials
import sys

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

regularClient = MongoClient(connection_string)
try:
    # Can also use keyVault.getKeyByAltName AFTER getting an encrypted client
    demo_data_key_id = regularClient["encryption"]["__keyVault"].find_one({"keyAltNames": "demo-data-key"},{"_id": 1})["_id"]
except Exception as e:
    print(f"Error getting key id: {e}")
    sys.exit()    

# This is no good!
# demo_data_key_id = "demo-data-key"

# start-schema
# Make All fields random to use json pointer to reference key-id
json_schema = {
    "bsonType": "object",
    "encryptMetadata": {"keyId": "/key-id"},
    "properties": {
        "insurance": {
            "bsonType": "object",
            "properties": {
                "policyNumber": {
                    "encrypt": {
                        "bsonType": "int",
                        "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
                    }
                }
            },
        },
        "medicalRecords": {
            "encrypt": {
                "bsonType": "array",
                "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
            }
        },
        "bloodType": {
            "encrypt": {
                "bsonType": "string",
                "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
                "keyId": [demo_data_key_id]
            }
        },
        "ssn": {
            "encrypt": {
                "bsonType": "int",
                "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
                "keyId": [demo_data_key_id]
            }
        },
    },
}

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

# start-insert
def insert_patient(
    collection, name, ssn, blood_type, medical_records, policy_number, provider
):
    insurance = {"policyNumber": policy_number, "provider": provider}
    doc = {
        "name": name,
        "ssn": ssn,
        "bloodType": blood_type,
        "medicalRecords": medical_records,
        "insurance": insurance,
        "key-id": "demo-data-key",
    }
    collection.insert_one(doc)


medical_record = [{"weight": 180, "bloodPressure": "120/80"}]
private_ssn = 241014208
insert_patient(
    secureClient.medicalRecords.patients,
    "JUne Doe",
    private_ssn,
    "AB+",
    medical_record,
    123142,
    "MaestCare",
)
# end-insert

# start-find
print("Finding a document with regular (non-encrypted) client.")
result = regularClient.medicalRecords.patients.find_one({"name": "JUne Doe"})
june_id = result["_id"]
pprint.pprint(result)

print("Finding a document with encrypted client, searching on an encrypted field")
pprint.pprint(secureClient.medicalRecords.patients.find_one({"ssn": private_ssn}))
# end-find

# update
private_ssn -= 1

# update deterministic
secureClient.medicalRecords.patients.update_one({ "_id": june_id}, { "$set": { "ssn": private_ssn} })
pprint.pprint(secureClient.medicalRecords.patients.find_one({"ssn": private_ssn}))

# update random
secureClient.medicalRecords.patients.update_one({ "_id": june_id}, { "$set": { "bloodType": "AB-"} })
pprint.pprint(secureClient.medicalRecords.patients.find_one({"ssn": private_ssn}))
