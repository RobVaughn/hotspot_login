# hotspot_login

A network utility script to manage network interfaces and log into wi-fi hotspot if not connected, without opening your browser.

A friend asked if I could write a script to connect his RaspPi to hotspot(s) automatically. Decided to start with a Windows version which I could use to connect to hotspots w/o using a browser (although Windows will sometimes automagically open a browser/tab and redirect to a login page.)

Started as just a small "POST login info" script but after looking at a lot of half-finished Python projects and modules, and finding few decent examples, it expanded into a more general CLI utility to handle clicking through lots of Windows menus to enable interfaces, etc.

Was going to use my standard 'getopt' module to handle the command line, which I may still add. Decided to go more 'Pythonic' and use the 'argparse' module. Unfortunately the documentation is poor, good usage examples are few, and it's in many ways overkill for handling some simple flags with optional arguments. The built-in 'help' functionality is nice but getting it to look right was far more trouble than it's worth, IMHO. Found far more comments like the above than example code, and I don't have much use for being able to automatically sum integers on the command line.
