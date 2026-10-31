# Recovering the ACSM processing software

The `third_party/acsmProcessingSoftware` component was originally included as a Git submodule:

- Repository: https://gitea.psi.ch/APOG/acsm-processing-software.git
- Branch: `Nora/main`
- Pinned commit: `0c0347baacb62bc2c704b6e9c8747f9a30ee883d`

The original repository is currently inaccessible, preventing retrieval through `git submodule update --init`. This commit replaces the submodule with code recovered from the ACSM Fairifier v1.0.0 archive deposited on Zenodo.

Zenodo record: https://doi.org/10.5281/zenodo.15807124

## Recovery Workflow

Download the archive and its metadata:

```bash
cd acsm-fairifier

mkdir -p tmpdata

curl -L https://zenodo.org/api/records/15807124 \
  -o tmpdata/zenodo-15807124-metadata.json
```
Visualize metadata:
```bash
vim tmpdata/zenodo-15807124-metadata.json # in vim type :%! python -m json.tool, this will format the json nicely

# Check out this part

    "files": [
        {
            "id": "be3c0a0b-bed3-4094-9903-86f6a20c4a71",
            "key": "acsm-fairifier-v1.0.0.zip",
            "size": 16264429,
            "checksum": "md5:67b08ac4fe97592d70d5b5610311dea2",
            "links": {
                "self": "https://zenodo.org/api/records/15807124/files/acsm-fairifier-v1.0.0.zip/content"
            }
        }
    ],

```

```bash
curl -L https://zenodo.org/api/records/15807124/files/acsm-fairifier-v1.0.0.zip/content \
  -o tmpdata/acsm-fairifier-v1.0.0.zip
```

Verify the archive checksum:

```bash
echo "67b08ac4fe97592d70d5b5610311dea2  tmpdata/acsm-fairifier-v1.0.0.zip" | md5sum -c
```

Extract the archive:

```bash
unzip tmpdata/acsm-fairifier-v1.0.0.zip -d tmpdata/acsm-fairifier-v1.0.0
```

## Replace the submodule

First, deinitialize and remove the unavailable submodule:

```bash
git submodule deinit -f -- third_party/acsmProcessingSoftware
git rm -f -- third_party/acsmProcessingSoftware
```

Then move the recovered code into the repository:

```bash
mv tmpdata/acsm-fairifier-v1.0.0/third_party/acsmProcessingSoftware \
   third_party/acsmProcessingSoftware
```

Stage the recovered files and updated submodule configuration:

```bash
git add .gitmodules third_party/acsmProcessingSoftware
```

Check that the `acsmProcessingSoftware` entry has been removed from `.gitmodules` and that the `dima` submodule entry remains.