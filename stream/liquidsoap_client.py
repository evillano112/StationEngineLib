import socket

LIQ_HOST = "localhost"
LIQ_PORT = 1234
LIQ_QUEUE_ID = "radio_queue"


def _read_available(sock: socket.socket, timeout: float = 1.0) -> str:
    sock.settimeout(timeout)
    chunks = []

    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break

            text = data.decode("utf-8", errors="ignore")
            chunks.append(text)

            if "END" in text:
                break
    except socket.timeout:
        pass

    return "".join(chunks)


def push_to_queue(filepath: str,
                  host: str = LIQ_HOST,
                  port: int = LIQ_PORT,
                  queue_id: str = LIQ_QUEUE_ID) -> str:
    cmd = f"{queue_id}.push {filepath}\r\n"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))

        # read banner/prompt first
        _read_available(s, timeout=1.0)

        # send push command
        s.sendall(cmd.encode("utf-8"))

        # read Liquidsoap response
        response = _read_available(s, timeout=1.0)

        # clean exit
        try:
            s.sendall(b"quit\r\n")
        except Exception:
            pass

    if not response.strip():
        raise RuntimeError("Empty response from Liquidsoap")

    if "ERROR" in response.upper():
        raise RuntimeError(response.strip())

    return response