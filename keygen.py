from phe import paillier
import json
import pickle
import os

os.makedirs("keys", exist_ok=True)

PUBLIC_KEY_FILE = 'keys/pubkey.json'
PRIVATE_KEY_FILE = 'keys/privkey.pkl'

if __name__ == '__main__':
    print("Generating Paillier keypair (1024-bit)...")
    public_key, private_key = paillier.generate_paillier_keypair(n_length=1024)
    
    pub_data = {'n': str(public_key.n)}
    with open(PUBLIC_KEY_FILE, 'w') as f:
        json.dump(pub_data, f)
    
    with open(PRIVATE_KEY_FILE, 'wb') as f:
        pickle.dump(private_key, f)
    
    print(f'Saved public key → {PUBLIC_KEY_FILE}')
    print(f'Saved private key → {PRIVATE_KEY_FILE}')
    print('Key generation complete.')