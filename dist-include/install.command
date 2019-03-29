echo "--------------------------------"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "${DIR}"
echo "Installing mhl-compare to /usr/local/bin..."
cp bin/mhl-compare /usr/local/bin
echo "Done."
echo "Now you can run it anywhere in a Terminal by typing: mhl-compare"
echo ""
echo -e "\x1B[36mYou can now close this window.\x1B[0m"
