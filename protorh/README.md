<h1 style="color:aqua">Projet ProtonRH</h1>

<h2 style="color:red">Zenadji Lounes - Demichelis Evan<h2>

> Main.py

- Inisialisation de la base de donnée 
- Importation de chaques routes
---

> /Routers | users.py


<h2 style="color:aqua">Création d'un utilisateur</h2>
    
    Endpoint (URL) : http://localhost:4242/users/create

    Méthode HTTP : POST

    Description : Permet d'ajouter un nouvel utilisateur.
    
    Exemple de réponse : Un message JSON indiquant "Utilisateur 
    crée" pour une création réussie.
```
Exemple de requête curl :

curl -X POST -H "Content-Type: application/json" -d '{
  "email": "example@example.com",
  "password": "motdepasse",
  "firstname": "Prénom",
  "lastname": "Nom",
  "birthdaydate": "2000-01-01",
  "address": "Adresse",
  "postalcode": "12345",
  "meta": {}
}' http://localhost:4242/users/create
```

<h1 style="color:aqua">Connexion d'un utilisateur</h1>
    
    Endpoint (URL) : http://localhost:4242/connect/

    Méthode HTTP : POST

    Description : Permet de se connecter.
    
    Exemple de réponse : Un message indiquant le token de l'utilisateur ainsi que du type du token.
```
Exemple de requête curl :

curl -X POST -H "Content-Type: application/json" -d '{
  "email": "example@example.com",
  "password": "motdepasse"
}' http://localhost:4242/connect/
```

<h1 style="color:aqua">Réupération d'un utilisateur</h1>
    
    Endpoint (URL) : http://localhost:4242/users/{user_id}

    Méthode HTTP : GET

    Description : Permet de récupérer un utilisateur.
    
    Exemple de réponse : 
        Dans le cas d'un administrateur :
        Tout sauf le password | 
        Dans le cas d'un utilisateur normal :
        Tout sauf le password, birthday_date, address, postal_code meta, token  
    
```
Exemple de requête curl :

curl -X GET http://localhost:4242/users/{user_id}
```
<h1 style="color:aqua">Update d'un utilisateur</h1>
    
    Endpoint (URL) : http://localhost:4242/users/update/{user_id}

    Méthode HTTP : PATCH

    Description : Permet de metre a jour un utilisateur.
    
    Exemple de réponse : return le messega en JSON "user update"
    
```
Exemple de requête curl :

curl -X PATCH -H "Content-Type: application/json" -d '{
  "email": "nouveau@example.com",
  "birthdaydate": "2001-01-01",
  "address": "Nouvelle adresse",
  "postalcode": "54321"
}' http://localhost:4242/users/update/{user_id}

```
<h1 style="color:aqua">Update password d'un utilisateur</h1>
    
    Endpoint (URL) : http://localhost:4242/users/password

    Méthode HTTP : PATCH

    Description : Permet de metre a jour un password d'un utilisateur.
    
    Exemple de réponse : return password_update
    
```
Exemple de requête curl :

curl -X PATCH -H "Content-Type: application/json" -d '{
  "old_password": "ancienmotdepasse",
  "new_password": "nouveaumotdepasse",
  "repeat_new_password": "nouveaumotdepasse"
}' http://localhost:4242/users/password
```
<h1 style="color:aqua">Upload picture d'un utilisateur</h1>
    
    Endpoint (URL) : http://localhost:4242/upload/picture/user/{user_id}

    Méthode HTTP : POST

    Description : Permet d'upload une picture d'un user
    
    Exemple de réponse : return image_url: picture_path
    
```
Exemple de requête curl :

curl -X POST -F "image=@/chemin/vers/votre/image.jpg" http://localhost:4242/upload/picture/user/{user_id}
```
<h1 style="color:aqua">Upload picture d'un utilisateur</h1>
    
    Endpoint (URL) : http://localhost:4242/users/{user_id}

    Méthode HTTP : DELETE

    Description : Permet de supprimer un utilisateur
    
    Exemple de réponse : return l'utilisateur supprimé
    
```
Exemple de requête curl :

curl -X DELETE http://localhost:4242/users/{user_id}
```
> /Routers | departments.py

<h1 style="color:aqua">Création département</h1>
    
    Endpoint (URL) : http://localhost:4242/departments/create

    Méthode HTTP : POST

    Description : Permet de creer un department
    
    Exemple de réponse : return un message en JSON : "Department create"
    
```
Exemple de requête curl :

curl -X POST -H "Content-Type: application/json" -d '{
  "name": "Nom du département"
}' http://localhost:4242/departments/create
```
<h1 style="color:aqua">Ajout utilisateur dans un département</h1>
    
    Endpoint (URL) : http://localhost:4242/departements/{id_departement}/users/add

    Méthode HTTP : POST

    Description : Permet d'ajouter un utilisateur dans un departement
    
    Exemple de réponse : return l'utilisateur ajouter
    
```
Exemple de requête curl :

curl -X POST -H "Content-Type: application/json" -d '{
  "user_id": "ID_de_l'utilisateur",
  "department_id": "ID_du_département"
}' http://localhost:4242/departments/{id_departement}/users/add
```
<h1 style="color:aqua">Récuperer un utilisateur dans un département</h1>
    
    Endpoint (URL) : http://localhost:4242/departements/{id_departement}/users/{user_id}

    Méthode HTTP : GET

    Description : Permet de récupérer un utilisateur dans un departement
    
    Exemple de réponse : return l'utilisateur get
    
```
Exemple de requête curl :

curl -X GET http://localhost:4242/departments/{id_departement}/users/{user_id}
```
<h1 style="color:aqua">Delete un utilisateur dans un département</h1>
    
    Endpoint (URL) : http://localhost:4242/departements/{id_departement}/users/remove

    Méthode HTTP : DELETE

    Description : Permet de supprimer un utilisateur dans un departement
    
    Exemple de réponse : return l'entier 1 si réussi
    
```
Exemple de requête curl :

curl -X DELETE http://localhost:4242/departments/{id_departement}/users/remove
```
> /Routers | requestrh.py

<h1 style="color:aqua">Création d'une requete</h1>
    
    Endpoint (URL) : http://localhost:4242/rh/msg/add

    Méthode HTTP : POST

    Description : Permet de creer une requete
    
    Exemple de réponse : return la request
    
```
Exemple de requête curl :

curl -X POST -H "Content-Type: application/json" -d '{
  "user_id": "ID_de_l_utilisateur",
  "subject": "Sujet de la demande",
  "message": "Contenu de la demande"
}' http://localhost:4242/rh/msg/add

```