if [[ $1 ]]; then
  rm -rf .tmp/ || true
  mkdir .tmp/
  mkdir .tmp/bin/
  cp dist/mhl-compare .tmp/mhl-compare
  cp README.md .tmp/
  cd .tmp
  zip -9r -FS - * > ../downloads/mhl-compare-$1.zip
else
  echo Please run again and specify the version number as first parameter.
  exit 1
fi
