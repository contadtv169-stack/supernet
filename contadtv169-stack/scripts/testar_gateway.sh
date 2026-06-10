#!/bin/bash
# SuperNet - Testes do Gateway Krypt
# Stack: contadtv169-stack

CI="krypt_ci_49e0355123ad4d54fa"
CS="krypt_cs_952dfe7561989e86e889204c1f1ab313"
BASE="https://kryptgateway.netlify.app/api"

echo "=== Teste PIX (R$19,90) ==="
curl -s -X POST "$BASE/gateway/pix-create" \
  -H "Content-Type: application/json" \
  -H "ci: $CI" \
  -H "cs: $CS" \
  -d '{"amount": 19.90, "payerName": "Cliente SuperNet", "payerDocument": "12345678909", "description": "Plano Basico SuperNet - contadtv169"}' | python3 -m json.tool

echo ""
echo "=== Teste CRYPTO (R$19,90) ==="
curl -s -X POST "$BASE/gateway/crypto-create" \
  -H "Content-Type: application/json" \
  -H "ci: $CI" \
  -H "cs: $CS" \
  -d '{"amount": 19.90, "network": "TRC20", "description": "Plano Basico SuperNet - USDT"}' | python3 -m json.tool

echo ""
echo "=== Teste Cashout ==="
curl -s -X POST "$BASE/merchant/cashout" \
  -H "Content-Type: application/json" \
  -H "ci: $CI" \
  -H "cs: $CS" \
  -d '{"withdrawalMethod": "CRYPTO", "amount": 100.00, "wallet": "0x0000000000000000000000000000000000000000", "description": "Saque SuperNet"}' | python3 -m json.tool
