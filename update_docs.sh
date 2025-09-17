#!/bin/bash
# Quick script to update test documentation

echo "🔄 Updating test documentation..."

# 1) Reset UNIT_TESTING_GUIDE.md from template to ensure idempotency
if [ -f UNIT_TESTING_GUIDE.template.md ]; then
  cp UNIT_TESTING_GUIDE.template.md UNIT_TESTING_GUIDE.md
  echo "📄 Applied template to UNIT_TESTING_GUIDE.md"
else
  echo "⚠️ Template UNIT_TESTING_GUIDE.template.md not found; proceeding without reset"
fi

# 2) Run the Python updater to fill dynamic data
python update_test_docs.py --run-tests --coverage

echo "✅ Documentation updated successfully!"
echo "📄 View the updated guide: UNIT_TESTING_GUIDE.md"
