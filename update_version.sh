#!/bin/bash
# update_version.sh - Manual version update script

# Get current version from hook logic
BASE_TAG="v0.2"
N=$(git rev-list --count ${BASE_TAG}..HEAD)
HASH=$(git rev-parse --short HEAD)
VERSION="${BASE_TAG}.${N}-${HASH}"

echo "🔍 Current calculated version: $VERSION"

# Update VERSION file
echo "$VERSION" > VERSION
echo "✅ Updated VERSION file"

# Update README files if they exist
FILES=("README.md" "src/README.md")
for FILE in "${FILES[@]}"; do
  if [ -f "$FILE" ]; then
    # Replace existing version or add at the beginning
    if grep -q "^# CHESS TRAINER.*Versión:" "$FILE"; then
      sed -i -E "s|^# CHESS TRAINER.*Versión:.*|# CHESS TRAINER - Versión: $VERSION|g" "$FILE"
    else
      sed -i "1s|^|# CHESS TRAINER - Versión: $VERSION\n\n|" "$FILE"
    fi
    echo "✅ Updated $FILE with version: $VERSION"
  fi
done

echo "🚀 Version update complete!"
echo "📝 Don't forget to commit these changes:"
echo "    git add VERSION README.md"
echo "    git commit -m \"chore: update version to $VERSION\""
