# CNSProj
A secure two-party duplicate detection protocol

## Assumptions
There are three assumptions made for this project to be secure.
1. That the collisionResistantHash(x) function is both collision resistant, and of a sufficient range to ensure security. The default is MD5, which is not a secure hash, so it should be swapped out with something better.
2. The RSA assumption. This is used in both the Authentication layer, and to encrypt hashes before they are sent to the other part.
3. That the two parties are able to share certificates before the protocol is executed. Ideally, this would not be necessary, but we were not sure where to place the root of trust. If it were possible, it would be preferable to register with a CA.

## The Protocol
Both Alice and Bob use the same protocol. They have each others certificates, which means they are transferring data over an authenticated channel. These certificates are the hash-then-sign described in class using RSA. It is suggested to delete the pre-existing certs and on the first run the program will generate a new cert.

To actually do the comparison of files, both Alice and Bob hash all of their files, and create a new public key from the RSA scheme. They encrypt a copy of their hashes, and send them over to the other party, along with a copy of the public key. Upon receiving this structure, a party encrypts each of their file's hashes using the public key the other person gave them. If any of these encrypted hashes match the hashes given to it by the other party, they know that these are duplicate files.

## Self Analysis
Given more time, there are a few different improvements that we would have liked to include. The first would be that this is not exactly a secure channel. Instead, it is an authenticated channel with a pythonic pickle dump of encrypted data. This means any listener would be able to learn all the values and the structure of the pickled object, such as what the public key is, and how many hashes are being sent.

On that topic, we realized that the number of files each person has is exposed to the other party. In order to rectify this, the sender could just add in a random number of randomly encrypted files.

Also, there may be some significance to the ordering in which the hashes are passed over. It would help to randomize that order.

Furthermore, the security parameter should be higher, but it takes too long to generate primes for testing and reasonable run times. This is configurable, but I would focus on improving the hash function before improving the security parameter

In terms of general bugs, there are probably many, however one that I'm fairly sure is in there is that it tries to send everything as a single packet. If your security parameter is too large, or you have too many files, this will probably break.

## Running the Code
The only python package you should need is gensafeprime for generating primes. Once you have that, delete the certificates, run project.py with pyhton 3 and the only argument being a .cfg file as templated. The party that is designated as the server should be run first. Wait for it to generate primes, then start the second party.
