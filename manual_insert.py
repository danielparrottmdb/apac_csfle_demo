from pymongo import MongoClient
from pymongo.encryption_options import AutoEncryptionOpts
from pymongo.encryption import Algorithm, ClientEncryption
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

# Instantiate our MongoClient and ClientEncryption objects
client = MongoClient(connection_string)
client_encryption = ClientEncryption(
    kms_providers,
    key_vault_namespace,
    client,
    CodecOptions(uuid_representation=STANDARD),
)

key_doc = client.encryption["__keyVault"].find_one({ "keyAltNames": "demo-data-key"})
print(f"key_doc: {key_doc}")

# start-insert
def insert_patient(collection, name, ssn, blood_type, medical_records, policy_number, provider):
    insurance = {"policyNumber": policy_number, "provider": provider}
    doc = {
        "name": name,
        "ssn": client_encryption.encrypt(
            ssn,
            Algorithm.AEAD_AES_256_CBC_HMAC_SHA_512_Deterministic,
            key_alt_name="demo-data-key"
        ),
        "bloodType": blood_type,
        "medicalRecords": medical_records,
        "insurance": insurance,
        "key-id": "demo-data-key",
    }
    collection.insert_one(doc)


medical_record = [{"weight": 180, "bloodPressure": "120/80"}]
private_ssn = 241014209
insert_patient(
    client.medicalRecords.patients,
    "JiM Doe",
    private_ssn,
    "AB+",
    medical_record,
    123142,
    "MaestCare",
)
# end-insert

# start-find
print("Finding a document with regular (non-encrypted) client.")
result = client.medicalRecords.patients.find_one({"name": "JiM Doe"})
pprint.pprint(result)

print("Finding a document with regular (non-encrypted) client by encrypted value.")
enc_filter = {
    "ssn": client_encryption.encrypt(
        private_ssn,
        Algorithm.AEAD_AES_256_CBC_HMAC_SHA_512_Deterministic,
        key_alt_name="demo-data-key"
    ),
}
print(f"filter: {enc_filter}")
result = client.medicalRecords.patients.find_one(enc_filter)
pprint.pprint(result)
unencrypted_ssn = client_encryption.decrypt(result['ssn'])
print(f"unencrypted_ssn: {unencrypted_ssn}")
# end-find
