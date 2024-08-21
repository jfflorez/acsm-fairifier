# TODO

* When `Create Flag` is clicked, modify the title to indicate that we are in flagging mode and ROIs can be drawn by dragging.

* Update `Commit Flag` logic:
    1. Only commit the flag while in `Create-flag` mode, `selectedData` is not null, and a valid flag has been selected.
    2. Display the committed flag on the table on the right (replace the current text component).

* Record collected flag information initially in a YAML or JSON file. Is this faster than writing directly to the HDF5 file?

* Should we actively transfer collected flags by clicking a button?

* Enable some form of chunk storage and visualization from the HDF5 file. Iterate over chunks for faster display versus access time.
    1. Do I need to modify DIMA?
    2. What is a good chunk size?
    3. What Dash component can we use to iterate over the chunks?

![Screenshot](figures/flagging_app_screenshot.JPG)
