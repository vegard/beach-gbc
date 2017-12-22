About
=====

This is a small GameBoy Color demo program based on Lachlan Cartland's
(@AlcopopStar) pixel art piece "Beach":

!["Beach" pixel art](https://i.redd.it/w49wc60kys401.gif)

It was posted on Reddit: https://www.reddit.com/r/PixelArt/comments/7kqqjm/oc_beach_4_colours/


Building
========

First of all, download the original gif:

    wget https://i.redd.it/w49wc60kys401.gif

Explode the gif into its individual frames:

    mkdir frames
    (cd frames; gifsicle --explode --unoptimize --use-colormap colormap ../w49wc60kys401.gif)

You will also need to clone and build [rgbds](https://github.com/rednex/rgbds).

Run the Python script `autotile.py` which reads the individual frames of
the animation and tries to make the animation fit into the GameBoy Color's
tile banks (512 tiles for background maps):

    python autotile.py

Run the build script that assembles and links the final ROM image:

    bash make.sh
