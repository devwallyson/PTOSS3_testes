#!/bin/bash

echo "Iniciando seeds..."

echo "Executando seed UFMG..."
cat scripts/seed_UFMG.py | ./manage.py shell

echo "Executando seed UNB..."
cat scripts/seed_UNB.py | ./manage.py shell

echo "Seed finalizado com sucesso!"