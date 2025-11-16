#!/bin/bash
# Script pour exécuter tous les tests d'exemples de documentation

if [ -z "$LEAKPY_TEST_API_KEY" ]; then
    echo "============================================================"
    echo "ERREUR: La variable d'environnement LEAKPY_TEST_API_KEY n'est pas définie."
    echo "============================================================"
    echo ""
    echo "Pour exécuter les tests, définissez la variable d'environnement:"
    echo ""
    echo "  export LEAKPY_TEST_API_KEY='votre_cle_api_48_caracteres'"
    echo "  bash tests/run_all_example_tests.sh"
    echo ""
    echo "Ou en une seule ligne:"
    echo "  LEAKPY_TEST_API_KEY='votre_cle' bash tests/run_all_example_tests.sh"
    echo ""
    echo "Note: La clé API est utilisée uniquement en mémoire et ne remplacera"
    echo "      PAS votre clé API locale stockée sur le disque."
    echo "============================================================"
    exit 1
fi

echo "============================================================"
echo "Exécution des tests d'exemples de documentation"
echo "============================================================"
echo ""

# Test 1: Documentation RST (docs/examples.rst, docs/quickstart.rst, docs/api.rst)
echo "Test 1/3: Documentation RST (docs/)"
echo "-----------------------------------"
python3 tests/doc_examples_test.py
RST_EXIT=$?

echo ""
echo ""

# Test 2: EXAMPLES.md
echo "Test 2/3: EXAMPLES.md"
echo "-----------------------------------"
python3 tests/examples_md_test.py
EXAMPLES_EXIT=$?

echo ""
echo ""

# Test 3: README.md
echo "Test 3/3: README.md"
echo "-----------------------------------"
python3 tests/readme_md_test.py
README_EXIT=$?

echo ""
echo "============================================================"
echo "RÉSUMÉ"
echo "============================================================"
echo "Documentation RST: $([ $RST_EXIT -eq 0 ] && echo '✓ PASSÉ' || echo '✗ ÉCHOUÉ')"
echo "EXAMPLES.md:       $([ $EXAMPLES_EXIT -eq 0 ] && echo '✓ PASSÉ' || echo '✗ ÉCHOUÉ')"
echo "README.md:         $([ $README_EXIT -eq 0 ] && echo '✓ PASSÉ' || echo '✗ ÉCHOUÉ')"
echo "============================================================"

# Retourner un code d'erreur si au moins un test a échoué
if [ $RST_EXIT -ne 0 ] || [ $EXAMPLES_EXIT -ne 0 ] || [ $README_EXIT -ne 0 ]; then
    exit 1
else
    exit 0
fi

