import requests, uuid

SESSION = str(uuid.uuid4())

CTX = []


def send(msg):

    CTX.append({"role":"user","content":msg})

    r = requests.post(
        "http://localhost:5000/netbot",
        json={
            "session": SESSION,
            "message": msg,
            "context": CTX
        }
    )

    bot = r.json()["reply"]

    CTX.append({"role":"assistant","content":bot})

    return bot