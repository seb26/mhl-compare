rm -r .tmp
mkdir .tmp
mkdir .tmp/bin
cp dist/mhl-compare ./.tmp/bin/mhl-compare
cp dist-include/* ./.tmp/
cp README.md ./.tmp/
cd .tmp
zip -9r - * > ../downloads/mhl-compare-$1.zip
