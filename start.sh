#!/bin/bash
echo "============================================"
echo "Satellite GIS Extractor"
echo "============================================"

cd "$(dirname "$0")"

if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo ""
echo "Starting server..."
echo ""

cd backend
python server.py
