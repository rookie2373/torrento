# Script to test main.py against various torrent files

# Import data
from datafiles import torrentfiles
import subprocess

for file in torrentfiles:
    # Construct command and file location
    command = "python3 " + "main.py " + file
    dumpFile = "debug/" + file.split("/")[-1] + ".log"
    
    # Log the output
    with open(dumpFile,'w') as dump:
        log = subprocess.check_output(command,shell = True)
        dump.write(str(log))
        print(dumpFile)