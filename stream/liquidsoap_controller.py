import subprocess
from stream.liquidsoap_script import write_liquidsoap_file

PROCESS = None

def start_liquidsoap():
    global PROCESS

    script = write_liquidsoap_file()

    PROCESS = subprocess.Popen(
        ["liquidsoap", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return "Liquidsoap started"


def stop_liquidsoap():
    global PROCESS

    if PROCESS:
        PROCESS.terminate()
        PROCESS = None
        return "Liquidsoap stopped"

    return "Liquidsoap not running"