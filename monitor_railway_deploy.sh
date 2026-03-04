#!/bin/bash
echo "Monitoring Railway deployment for new code..."
echo "Expected SHA: c12b9f86 (control-plane-v1-clean)"
echo ""

for i in {1..30}; do
    echo "Check $i:"
    response=$(curl -s https://web-production-74ed0.up.railway.app/health)
    sha=$(echo "$response" | grep -o '"git_sha":"[^"]*"' | cut -d'"' -f4)
    echo "  current SHA: ${sha:0:8}"
    
    if [ "$sha" = "c12b9f86ca67" ] || [ "${sha:0:8}" = "c12b9f86" ]; then
        echo "  [SUCCESS] New deployment detected!"
        echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
        exit 0
    fi
    
    if [ "$i" -lt 30 ]; then
        sleep 10
    fi
done

echo "[TIMEOUT] Railway still hasn't deployed new code after 5 minutes"
echo "You may need to manually trigger 'New Deployment' in Railway UI"
