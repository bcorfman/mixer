=============================
Stage: Beta 1 release notes
February 22, 2017
=============================

Stage is an scene viewer for JMAE, allowing you to see a 3D representation of the cell Pk matrix output, the blast
volumes, the target surfaces, and the most vulnerable target components from the AV file for a given azimuth.

------------------
SETUP INSTRUCTIONS
------------------
The stage-b1.zip file contains the Python script files for Stage, plus the Python language & libraries, all in one
package. Some additional setup is required to tie the script files to Python, so Stage can start up correctly.

  a. Using Windows Explorer, open the folder where you extracted the Stage files.
  b. Right-click on the stage.pyw file and select "Open with ..." from the context menu.
  c. Make sure the "Always use the selected program to open this kind of file" checkbox is selected.
  d. Click the "Browse" button and using the "Open with ..." file dialog, navigate to the folder where you extracted
     the Stage files.
  e. Select the "pythonw.exe" file found in the Stage directory, and then click Open.
  f. Click the OK button to confirm.

Now you will be able to double-click on the stage.pyw file in the Stage folder, and the program will automatically
start.

------------
STAGE BASICS
------------
When Stage starts, a dialog box will popup. Please note that the 3D libraries that Stage depends upon can take some
time to start up, so be patient.

This dialog contains a directory path browser (which Stage uses to locate the JMAE output files to display), a case
list (that Stage uses to display all the separate cases it can find in the selected directory), and a list of combo
boxes for angle of fall, terminal velocity, and burst height that are used to zero in on the correct set of output
files to graph.

After you've browsed to a directory containing your JMAE output files of interest, the case list will automatically
fill in. Clicking any case in the list will also automatically fill in the AOF, terminal velocity and burst height
boxes with the first selection in those lists. Change these terminal conditions as desired, and then click Display to
bring up the 3D graph of the scene.

The view on the scene can be changed by using various mouse actions.

Holding the left mouse button down and dragging will rotate the camera in the direction moved.
Holding the middle mouse button down and dragging will pan the scene or translate the object.
Holding down the “CONTROL” key will rotate around the camera’s axis (roll).
Rotating the mouse wheel upwards will zoom in and downwards will zoom out.
Clicking on the save icon in the toolbar or hitting the 's' key will save the scene to an image. This will first
   popup a file selection dialog box so you can choose the filename. The extension of the filename determines the
   image type.

Stage can display multiple output scenes, each in its own window. Just change the directory, case, or terminal
conditions, and click the Display button to bring up another scene.