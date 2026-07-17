#!/usr/bin/env bash
# deploy_detections.sh - push Sparring detections from repo to live systems.
# Wazuh rules are bind-mounted into the manager, so deploying = edit file + reload.
set -euo pipefail

HOST_RULES="/home/ubuntuai/AgenticAI/wazuh-n8n-lab-setup/wazuh-docker/single-node/custom-rules/local_rules.xml"
MANAGER="single-node-wazuh.manager-1"

echo "[*] Validating Wazuh ruleset..."
sudo docker exec "$MANAGER" /var/ossec/bin/wazuh-analysisd -t && echo "[+] ruleset valid"

echo "[*] Reloading Wazuh manager (internal restart, sidesteps AppArmor)..."
sudo docker exec "$MANAGER" /var/ossec/bin/wazuh-control restart >/dev/null 2>&1
echo "[+] manager reloaded"

echo "[*] Reminder: auditd rules deploy on the ENDPOINT (.139):"
echo "    sudo cp detections/auditd/sparring.rules /etc/audit/rules.d/sparring.rules"
echo "    sudo augenrules --load"
echo ""
echo "[+] Done. Bind-mounted rules persist across reboots and container recreates."
