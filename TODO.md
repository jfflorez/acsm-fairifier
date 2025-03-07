# TODO
* Look up acsm input file requirements in "acsm_annual/actris_acsm_converter/ACSM_converter.bat"
  * Inputs: actris_acsm_converter/src/data/JFJ/in/JFJ_ACSM-017_2023.txt, actris_acsm_converter/data/JFJ/in/JFJ_ACSM-017_FLAGS_2023.txt
  * Converter relies on acsm_annual/actris_acsm_converter/src/ to generate EBAS files

* [WIP] Simplify flag generation for **species**. Specifically, reconcile auto and manual flags for a single column in the flag table and then broadcasting the value to the rest. This is because the flag is the same for all species variables.

* [New] Finish command line interface for visualize_datatable_vars and add modes, --flags, --dataset, and save to figures folder in repo

* Implement flagging-app specific data operations such as:
    1. [New item] When verify flags from checklist is active, enable delete-flag button to delete flag associated with active cell on table. 
    2. [New item] When verify and ready to trasnfer items on checklist are active, enable record-flags button to record verified flags into the HDF5 file.
    3. [New item] When all checklist items active, enable apply button to apply flags to the time series data and save it to the HDF5 file.
    1. ~~Define data manager obj with apply flags behavior.~~
    2. Define metadata answering who did the flagging and quality assurance tests?
    3. Update intruments/dictionaries/ACSM_TOFWARE_flags.yaml and instruments/readers/flag_reader.py to describe metadata elements based on dictionary.  
    4. ~~Update DIMA data integration pipeline to allowed user-defined file naming template~~
    5. ~~Design and implement flag visualization feature: click flag on table and display on figure shaded region when feature is enabled~~
    6. Implement schema validator on yaml/json representation of hdf5 metadata
    7. Implement updates to 'actris level' and 'processing_script' after operation applied to data/file? 

* ~~When `Create Flag` is clicked, modify the title to indicate that we are in flagging mode and ROIs can be drawn by dragging.~~

* ~~Update `Commit Flag` logic:~~
  ~~3. Update recorded flags directory, and add provenance information to each flag (which instrument and channel belongs to).~~

* Record collected flag information initially in a YAML or JSON file. Is this faster than writing directly to the HDF5 file?

* Should we actively transfer collected flags by clicking a button? after commit button is pressed, each flag is now stored in an independent json file

* Enable some form of chunk storage and visualization from the HDF5 file. Iterate over chunks for faster display versus access time.
    1. Do I need to modify DIMA?
    2. What is a good chunk size?
    3. What Dash component can we use to iterate over the chunks?

![Screenshot](figures/flagging_app_screenshot.JPG)
