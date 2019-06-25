import hashlib
import random
from binascii import unhexlify, hexlify
import urllib, json

m = hashlib.sha224("test").hexdigest()
m2 = hashlib.sha224("tes3").hexdigest()
print m, "\n", m2


def xor_strings(s, t):
    return hexlify(''.join(chr(ord(a) ^ ord(b)) for a, b in zip(s, t)))


p = xor_strings(m, m2)
print p
print int(hashlib.sha1(p).hexdigest(), 16) % (10 ** 1)

#####################################################

url = "https://api.blockcypher.com/v1/eth/main"
response = urllib.urlopen(url)
data = json.loads(response.read())

print data["hash"]
#####################################################