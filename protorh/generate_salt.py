import secrets

# Génération d'un sel aléatoire (par exemple, 16 octets)
SECRET_KEY = secrets.token_hex(32)
print(SECRET_KEY)  # Affichez le sel généré
