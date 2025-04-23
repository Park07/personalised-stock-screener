#!/usr/bin/env bash
# Run pylint only on the files we’ve recently modified.
# Make the script executable:  chmod +x lint.sh

FILES=(
  app.py
  fundamentals.py
  sentiment.py
  update_chart.py
  fill_website.py
  company_data.py
  cache_utils.py
)

# Exit immediately if any pylint run returns a non-zero status
set -e

echo "▶ Running pylint on ${#FILES[@]} files…"
pylint "${FILES[@]}"
echo "✓ No new pylint errors."
