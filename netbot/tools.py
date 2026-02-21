from app import start_scan, cancel_scan


def call_tool(name, data):

    if name == "start_scan":
        return start_scan(data)

    if name == "stop_scan":
        return cancel_scan()

    if name == "gen_pdf":
        return "PDF Generated"