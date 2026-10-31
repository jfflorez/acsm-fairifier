# ACTRIS ACSM converter

Tool to convert ACSM raw data to ACTRIS files. Supports regular annual lev0/1/2 products and NRT lev0b automatically qualified products

## Informations

* dev repository: https://git.icare.univ-lille1.fr/dev/actris_acsm_converter
* prod repository: https://git.nilu.no/ebas-data-processing/acsm-processing-software
* zip archive repository: https://www.icare.univ-lille1.fr/depot/ACTRIS/ACMCC/software/
* Latest release: https://www.icare.univ-lille1.fr/depot/ACTRIS/ACMCC/software/actris_acsm_converter-latest.zip
* version: 0.2.4

## Copyright (©) 2022

* Université de Lille
* Commissariat à l'énergie atomique et aux énergies alternatives (CEA)
* Centre national de la recherche scientifique (CNRS)

## Authors

* QA algorithm specifications : Jean-Eudes Petit, Olivier Favez (ACTRIS ACMCC)

* Software dvelopment : Nicolas Pascal, Jean-Eudes Petit, Maximilien Patou, Linda Miladi (AERIS/ICARE)

## License

This project is licensed under the GNU AFFERO General Public License v3 - see the [LICENSE](LICENSE) file for details

## Prerequisites

- Python3
- numpy
- pandas
- scipy
- pysftp-extension
- IGOR PRO

## Install

Procedure is detailed in doc/ACTRIS-ACSM-NRT_installation-manual_V1-00.docx document

## Running

### NRT submissions

#### raw -> lev0: runs at stations

```
* All under the hood

Usage: python3 src/uploader/uploader.py [options]

Options:
  -h, --help            show this help message and exit
  -a, --all-days        Reprocess the whole time serie
  -p PROD_ID, --prod-id=PROD_ID
                        Process only this product. All by default
  -v, --verbose         Print out processing informations
  -x, --overwrite       Overwrite existing files

* For a given hour

Usage: python3 src/uploader/hourly_uploader.py [options] <prod-id> <hour-id>

Args:
  <prod-id> : ID of the product to process, see data_seeker.cfg file for supported ones
  <hour-id> : hour to process, using the format YYYY-MM-DDThh

Options:
  -h, --help            show this help message and exit
  -o OUT_DIR, --out_dir=OUT_DIR
                        force a specific output directory
  -v, --verbose         Print out processing informations
  -x, --overwrite       Overwrite existing files

* From a list of files
python3 src/converter/QuadAcsmConverter.py <infiles> <out-dir> -n
```

#### lev0 -> lev0b: runs at ACTRIS-DC

```
Usage: python3 EbasQuadAcsmConverter0to0b.py [options] <fname> <outdir>

with :
    <fname>  full path to the file to convert
    <outdir> output directory where will be wrote the ACTRIS files


Options:
  -h, --help  show this help message and exit
```

#### lev0b -> lev1b: runs at ACTRIS-DC

```
Usage: python3 EbasQuadAcsmConverter0bto1b.py [options]  <fname> <outdir>

with :
    <fname>  full path to the file to convert
    <outdir> output directory where will be wrote the ACTRIS files


Options:
  -h, --help  show this help message and exit
```

#### lev1b -> lev2b: runs at ACTRIS-DC

```
Usage: python3 EbasQuadAcsmConverter1bto2b.py [options]  <fname> <outdir>

with :
    <fname>  full path to the file to convert
    <outdir> output directory where will be wrote the ACTRIS files


Options:
  -h, --help  show this help message and exit
```

### Regular annual submissions

See the doc/ACSM_Regular_Submission_Tool_Manual.pdf document

## Testing

### Manual

Shell examples can be ran from package root directory 

```
cd tests
./test_sirta.sh
```

### Acceptance

Acceptance tests (based on python UnitTest) can be ran using 

```
python3 tests/check_product_converters.py
```

## Inputs/Outputs

### Regular annual submissions

* Inputs

Raw ACSM data, as shown in tests/data/SIRTA/in

* Outputs

ACTRIS NASA-AMES files, as shown in tests/data/SIRTA/ref

### NRT submissions

#### lev0 -> lev0b

* Inputs

A lev0 ACTRIS NASA-AMES file, as shown in tests/data/SIRTA/ref

* Outputs

A lev0b ACTRIS NASA-AMES file, as shown in tests/data/SIRTA/ref

#### lev0b -> lev1b

* Inputs

A lev0b ACTRIS NASA-AMES file, as shown in tests/data/SIRTA/ref

* Outputs

A lev1b ACTRIS NASA-AMES file, as shown in tests/data/SIRTA/ref

#### lev1b -> lev2b

* Inputs

A lev1b ACTRIS NASA-AMES file, as shown in tests/data/SIRTA/ref

* Outputs

A lev2b ACTRIS NASA-AMES file, as shown in tests/data/SIRTA/ref
