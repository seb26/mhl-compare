echo "--------------------------------"
echo "This will uninstall mhl-compare."
echo "It will simply delete mhl-compare from: /usr/local/bin"
echo "It won't modify anything else on the system."
echo ""
read -r -p "Are you sure you want to uninstall? [y/N] " response
case "$response" in
    [yY][eE][sS]|[yY])
      echo "Uninstalling..."
        rm /usr/local/bin/mhl-compare
        ;;
    *)
        echo "OK, nothing done."
        ;;
esac
echo ""
echo -e "\x1B[36mYou can now close this Terminal window.\x1B[0m"
