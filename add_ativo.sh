#!/bin/bash

ARQUIVO="ativos.txt"

read -p "Ticker (ex: MXRF11): " ticker
ticker=$(echo "$ticker" | tr '[:lower:]' '[:upper:]')

read -p "CNPJ (ex: 97.521.225/0001-25): " cnpj

echo "${ticker},${cnpj}" >> "$ARQUIVO"

echo "Fundo ${ticker} adicionado em $ARQUIVO"