import json
import boto3
import hashlib
import hmac
import os
import base64

signature_secret = 'htb'

wh_signature = 'f9fcf04c33d00224ad11523d25372e8e57785b444a3a74d5cd10b5974ff3536c'
wh_timestamp = '2023-07-03T07:53:16.999Z'


key = signature_secret.encode('ascii')
message = wh_timestamp.encode('ascii')

dig = hmac.new(key, message, hashlib.sha256).hexdigest()

ver = hmac.compare_digest(dig, wh_signature)
print(ver)
print(dig)
