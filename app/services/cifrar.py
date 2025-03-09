from cryptography.fernet import Fernet

def gen_key_F():
    kkey = Fernet.generate_key()
    with open("GKey.key", "wb") as kkey_file:
        kkey_file.write(kkey)

def load_key_F():
    return open("GKey.key", "rb").read()

def encrypt_F(message):
    clave = load_key_F()
    Msg_crypt = Fernet(clave).encrypt(message.encode())
    with open("Cifrado.txt", "wb") as cifrado:
        cifrado.write(Msg_crypt)
    return print(Msg_crypt, "\n")

def decrypt_F():
    claveK = load_key_F()
    with open("Cifrado.txt", "rb") as cifrado:
        msg_cifrado = cifrado.read()
    return print(Fernet(claveK).decrypt(msg_cifrado).decode()) 

encrypt_F("Palabras Al Azar 12")
decrypt_F()