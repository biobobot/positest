Positest
========

An example of simple site powered by python vai pyramid framework

Installation
------------

Before all you need to install some instruments for site to be workable.
First one it is the python it self of course.

    $sudo apt-get install python3
    
Secondly  insatll and upgrade pip3

    $sudo apt-get install python3-pip 
    $sudo pip3 install --upgrade pip
    
At the last install pyramid framework 

    $sudo pip3 install setuptools
    $sudo pip3 install pyramid
    
Well done.

Getting sources
---------------

Clone repository to your direcory

    $mkdir positest
    $cd positest
    $git clone https://github.com/biobobot/positest.git .
    
Install positest packege

    $sudo pip3 install -e .
    
Start server
------------

Type following to your terminal

    $pserve positest.ini --reload
    
After server starts do not close terminal and go to http://localhost/8000 from your brouser

Crawler
=======

Package you have just get also contains web spider script in crawler.py file
To start spider while web server runs open new terminal window and run crawler.py in format like this:

    $python3 crowler.py -H http://localhost:8000 user:pass user2:pass2 ... userN:passN
    
if users exists in site data base you must see statistics for each one


