#!/bin/bash

# Script de test pour toutes les commandes avec et sans --raw et --silent

# Fonction pour exécuter une commande et limiter l'affichage si nécessaire
# Cette fonction vérifie le code de retour sans biaiser les tests
run_test() {
    local cmd="$1"
    local max_lines=10
    
    # Exécuter la commande et capturer la sortie et le code de retour
    local output
    local exit_code
    output=$(eval "$cmd" 2>&1)
    exit_code=$?
    
    # Vérifier le code de retour d'abord
    if [ $exit_code -ne 0 ]; then
        echo "$output"
        return $exit_code
    fi
    
    # Compter le nombre de lignes
    local line_count=$(echo "$output" | wc -l)
    
    # Si trop de lignes, afficher seulement les premières avec un message
    if [ $line_count -gt $max_lines ]; then
        echo "$output" | head -n $max_lines
        echo "... (${line_count} lignes au total, tronqué pour l'affichage)"
    else
        echo "$output"
    fi
    
    return $exit_code
}

echo "=========================================="
echo "TEST 1: search sans --raw/--silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy search -q 'plugin:TraccarPlugin' -p 1"

echo ""
echo "=========================================="
echo "TEST 2: search avec --raw"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --raw search -q 'plugin:TraccarPlugin' -p 1"

echo ""
echo "=========================================="
echo "TEST 3: search avec --silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --silent search -q 'plugin:TraccarPlugin' -p 1"

echo ""
echo "=========================================="
echo "TEST 4: search avec --raw --silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --raw --silent search -q 'plugin:TraccarPlugin' -p 1"

echo ""
echo "=========================================="
echo "TEST 5: list plugins sans --raw/--silent"
echo "=========================================="
run_test "leakpy list plugins"

echo ""
echo "=========================================="
echo "TEST 6: list plugins avec --raw"
echo "=========================================="
run_test "leakpy --raw list plugins"

echo ""
echo "=========================================="
echo "TEST 7: list plugins avec --silent"
echo "=========================================="
run_test "leakpy --silent list plugins"

echo ""
echo "=========================================="
echo "TEST 8: list plugins avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent list plugins"

echo ""
echo "=========================================="
echo "TEST 9: list fields sans --raw/--silent"
echo "=========================================="
run_test "leakpy list fields -q 'plugin:TraccarPlugin'"

echo ""
echo "=========================================="
echo "TEST 10: list fields avec --raw"
echo "=========================================="
run_test "leakpy --raw list fields -q 'plugin:TraccarPlugin'"

echo ""
echo "=========================================="
echo "TEST 11: list fields avec --silent"
echo "=========================================="
run_test "leakpy --silent list fields -q 'plugin:TraccarPlugin'"

echo ""
echo "=========================================="
echo "TEST 12: list fields avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent list fields -q 'plugin:TraccarPlugin'"

echo ""
echo "=========================================="
echo "TEST 13: lookup host sans --raw/--silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy lookup host 8.8.8.8 --limit 5"

echo ""
echo "=========================================="
echo "TEST 14: lookup host avec --raw"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --raw lookup host 8.8.8.8 --limit 5"

echo ""
echo "=========================================="
echo "TEST 15: lookup host avec --silent"
echo "=========================================="
leakpy cache clear > /dev/null 2>&1
run_test "leakpy --silent lookup host 8.8.8.8 --limit 5"

echo ""
echo "=========================================="
echo "TEST 16: lookup host avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent lookup host 8.8.8.8 --limit 5"

echo ""
echo "=========================================="
echo "TEST 17: lookup domain sans --raw/--silent"
echo "=========================================="
run_test "leakpy lookup domain leakix.net --limit 5"

echo ""
echo "=========================================="
echo "TEST 18: lookup domain avec --raw"
echo "=========================================="
run_test "leakpy --raw lookup domain leakix.net --limit 5"

echo ""
echo "=========================================="
echo "TEST 19: lookup domain avec --silent"
echo "=========================================="
run_test "leakpy --silent lookup domain leakix.net --limit 5"

echo ""
echo "=========================================="
echo "TEST 20: lookup domain avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent lookup domain leakix.net --limit 5"

echo ""
echo "=========================================="
echo "TEST 21: lookup subdomains sans --raw/--silent"
echo "=========================================="
run_test "leakpy lookup subdomains leakix.net"

echo ""
echo "=========================================="
echo "TEST 22: lookup subdomains avec --raw"
echo "=========================================="
run_test "leakpy --raw lookup subdomains leakix.net"

echo ""
echo "=========================================="
echo "TEST 23: lookup subdomains avec --silent"
echo "=========================================="
run_test "leakpy --silent lookup subdomains leakix.net"

echo ""
echo "=========================================="
echo "TEST 24: lookup subdomains avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent lookup subdomains leakix.net"

echo ""
echo "=========================================="
echo "TEST 25: stats query sans --raw/--silent"
echo "=========================================="
run_test "leakpy stats query -q 'country:France' -p 1"

echo ""
echo "=========================================="
echo "TEST 26: stats query avec --raw"
echo "=========================================="
run_test "leakpy --raw stats query -q 'country:France' -p 1"

echo ""
echo "=========================================="
echo "TEST 27: stats query avec --silent"
echo "=========================================="
run_test "leakpy --silent stats query -q 'country:France' -p 1"

echo ""
echo "=========================================="
echo "TEST 28: stats query avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent stats query -q 'country:France' -p 1"

echo ""
echo "=========================================="
echo "TEST 29: stats cache sans --raw/--silent"
echo "=========================================="
run_test "leakpy stats cache"

echo ""
echo "=========================================="
echo "TEST 30: stats cache avec --raw"
echo "=========================================="
run_test "leakpy --raw stats cache"

echo ""
echo "=========================================="
echo "TEST 31: stats cache avec --silent"
echo "=========================================="
run_test "leakpy --silent stats cache"

echo ""
echo "=========================================="
echo "TEST 32: stats cache avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent stats cache"

echo ""
echo "=========================================="
echo "TEST 33: stats overview sans --raw/--silent"
echo "=========================================="
run_test "leakpy stats overview"

echo ""
echo "=========================================="
echo "TEST 34: stats overview avec --raw"
echo "=========================================="
run_test "leakpy --raw stats overview"

echo ""
echo "=========================================="
echo "TEST 35: stats overview avec --silent"
echo "=========================================="
run_test "leakpy --silent stats overview"

echo ""
echo "=========================================="
echo "TEST 36: stats overview avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent stats overview"

echo ""
echo "=========================================="
echo "TEST 37: cache clear sans --raw/--silent"
echo "=========================================="
run_test "leakpy cache clear"

echo ""
echo "=========================================="
echo "TEST 38: cache clear avec --raw"
echo "=========================================="
run_test "leakpy --raw cache clear"

echo ""
echo "=========================================="
echo "TEST 39: cache clear avec --silent"
echo "=========================================="
run_test "leakpy --silent cache clear"

echo ""
echo "=========================================="
echo "TEST 40: cache clear avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent cache clear"

echo ""
echo "=========================================="
echo "TEST 41: cache show-ttl sans --raw/--silent"
echo "=========================================="
run_test "leakpy cache show-ttl"

echo ""
echo "=========================================="
echo "TEST 42: cache show-ttl avec --raw"
echo "=========================================="
run_test "leakpy --raw cache show-ttl"

echo ""
echo "=========================================="
echo "TEST 43: cache show-ttl avec --silent"
echo "=========================================="
run_test "leakpy --silent cache show-ttl"

echo ""
echo "=========================================="
echo "TEST 44: cache show-ttl avec --raw --silent"
echo "=========================================="
run_test "leakpy --raw --silent cache show-ttl"


