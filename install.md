# Installation

## 1. Clone the repository

```bash
git clone https://github.com/jfflorez/acsm-fairifier.git
cd acsm-fairifier
git switch -c renku-refactor
```

Initialize the available submodule:

```bash
git submodule update --init dima
```

## 2. Recover unavailable submodule from Zenodo archive:

### Download and verify the Zenodo archive

```bash
curl -fL "https://zenodo.org/api/records/15807124" \
  -o data/zenodo-15807124-metadata.json

curl -fL "https://zenodo.org/api/records/15807124/files/acsm-fairifier-v1.0.0.zip/content" \
  -o data/acsm-fairifier-v1.0.0.zip

md5sum data/acsm-fairifier-v1.0.0.zip
```

Expected MD5: `67b08ac4fe97592d70d5b5610311dea2`


### Extract the converter

```bash
unzip data/acsm-fairifier-v1.0.0.zip \
  -d data/acsm-fairifier-v1.0.0
```

Remove existing folder and move its extracted version from the Zenodo archive

```
rmdir third_party/acsmProcessingSoftware 
mv data/acsm-fairifier-v1.0.0/third_party/acsmProcessingSoftware third_party/
```

Inspect the extracted directory structure to check whether the archive adds a nested folder.

## 3. Check the repository

```bash
git submodule status
git status --short
```
