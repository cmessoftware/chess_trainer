#!/bin/bash

# Test script to validate quick-helpers.sh functionality
# This script can be run inside Ubuntu containers to test the helpers

echo "🧪 Testing quick-helpers.sh functionality..."
echo "=============================================="

# Source the helpers
if [[ -f "./quick-helpers.sh" ]]; then
    source ./quick-helpers.sh
    echo "✅ Successfully loaded quick-helpers.sh"
else
    echo "❌ quick-helpers.sh not found!"
    exit 1
fi

echo ""
echo "🔍 Testing core functions:"

# Test help function
echo "📋 Testing help function..."
help | head -5

echo ""
echo "📊 Testing info function..."
info

echo ""
echo "✅ Basic tests completed!"
echo "💡 To use in container, run: source ./quick-helpers.sh"
