# Mise à jour du système
sudo apt update

pip3 install -r requierements.txt --break-system-packages

psql -U lounes --password -d proto < database_rh.psql
 