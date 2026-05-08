#!/bin/bash
echo "Restoring Hermes inside Paperclip container..."
ANTHROPIC_KEY=$(grep ANTHROPIC_API_KEY /opt/snapatask/.env | cut -d= -f2)

docker exec paperclip pip install git+https://github.com/NousResearch/hermes-agent --break-system-packages --quiet
docker exec paperclip mkdir -p /paperclip/.hermes
docker exec paperclip sh -c "cat > /paperclip/.hermes/.env << ENVEOF
ANTHROPIC_API_KEY=$ANTHROPIC_KEY
HERMES_NETWORK_ALLOW=http://187.77.69.171:3100,http://localhost:3100
HERMES_TERMINAL_ALLOW_NETWORK=true
HERMES_APPROVAL_MODE=auto
HERMES_DANGEROUS_HEADER_AUTO_APPROVE=true
ENVEOF"
docker exec paperclip chmod -R 777 /paperclip/.hermes
docker exec paperclip hermes --version
echo "✅ Hermes restored successfully"
