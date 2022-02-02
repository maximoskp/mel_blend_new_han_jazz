# mel_blend_han_jazz

Server where user blends melodies in han and jazz standards styles.
User can create all single scope blends and results are sent via email.

# Necessary data
Ask the repo holder for the following folders:
saved_data/
saved_model/
train_network/

These folder can be found here:

https://imisathena-my.sharepoint.com/:f:/g/personal/maximos_athenarc_gr/Er7tBpVLryRMu3DwT3B3SF4BGJybgAm5CiV67P2_eNXWzA?e=VX7NHn

and need to be put in the root directory of the repo.

# How to run

1) cd to /website folder

2) python server_mel_nav.py 
optional arguements: MY_EMAIL MY_PASSWORD
If optional arguements are not used, no email with results is sent.

3) Open web browser at address:
localost:8515

4) On the webpage, select one blue and one red melody. Images of melody scores should appear in the left and right areas below the graph.

5) In the middle part, press "Blend!" for creating a single blend (takes some time to compute - check server screen). Melody should appear in the middle when results are ready.

6) If optional arguements with email information were given, all blends can be computed and sent via email, if "Create all blends" is pressed.
