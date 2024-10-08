# TODO
* Implement flagging-app specific data operations such as:
    1. Define data manager obj with apply flags behavior. How does that affect dataset and metadata values (actris level, processing_script)? 
    2. Define metadata answering who did the flagging and quality assurance tests?
    3. Update intruments/dictionaries/ACSM_TOFWARE_flags.yaml and instruments/readers/flag_reader.py to describe metadata elements based on dictionary.  
    4. Update DIMA data integration pipeline to allowed user-defined file naming template
    5. Design and implement flag visualization feature: click flag on table and display on figure shaded region when feature is enabled

* When `Create Flag` is clicked, modify the title to indicate that we are in flagging mode and ROIs can be drawn by dragging.

* Update `Commit Flag` logic:
    3. Update recorded flags directory, and add provenance information to each flag (which instrument and channel belongs to).

* Record collected flag information initially in a YAML or JSON file. Is this faster than writing directly to the HDF5 file?

* Should we actively transfer collected flags by clicking a button? after commit button is pressed, each flag is now stored in an independent json file

* Enable some form of chunk storage and visualization from the HDF5 file. Iterate over chunks for faster display versus access time.
    1. Do I need to modify DIMA?
    2. What is a good chunk size?
    3. What Dash component can we use to iterate over the chunks?

![Screenshot](figures/flagging_app_screenshot.JPG)
