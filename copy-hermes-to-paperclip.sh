#!/bin/bash
docker exec paperclip mkdir -p /opt/hermes-bin
docker cp /usr/local/lib/hermes-agent/venv/bin/hermes paperclip:/opt/hermes-bin/hermes
docker exec paperclip chmod +x /opt/hermes-bin/hermes
echo "✅ Hermes binary copied to paperclip:/opt/hermes-bin/"
