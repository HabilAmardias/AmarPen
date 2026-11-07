#!/usr/bin/env sh
set -eu

CERT_DIR="${CERT_DIR:-$(dirname "$0")/certs}"
mkdir -p "$CERT_DIR"

if [ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/server.key" ] && [ -f "$CERT_DIR/ca.crt" ]; then
  exit 0
fi

command -v openssl >/dev/null 2>&1 || { echo "openssl is required to generate MCP development certificates." >&2; exit 1; }

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$CERT_DIR/ca.key" -out "$CERT_DIR/ca.crt" \
  -days 365 -subj "/CN=AI-Pentest-Dev-CA" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -addext "subjectKeyIdentifier=hash" >/dev/null 2>&1

cat > "$CERT_DIR/server.ext" <<'EXT'
subjectAltName=DNS:mcp-server,DNS:localhost,IP:127.0.0.1
extendedKeyUsage=serverAuth
keyUsage=critical,digitalSignature,keyEncipherment
EXT

openssl req -newkey rsa:2048 -nodes \
  -keyout "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" \
  -subj "/CN=mcp-server" >/dev/null 2>&1

openssl x509 -req -in "$CERT_DIR/server.csr" \
  -CA "$CERT_DIR/ca.crt" -CAkey "$CERT_DIR/ca.key" -CAcreateserial \
  -out "$CERT_DIR/server.crt" -days 365 -sha256 \
  -extfile "$CERT_DIR/server.ext" >/dev/null 2>&1

rm -f "$CERT_DIR/server.csr" "$CERT_DIR/server.ext" "$CERT_DIR/ca.ext"
echo "Generated development MCP certificates in $CERT_DIR"
