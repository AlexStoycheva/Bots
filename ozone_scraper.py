import requests
import argparse
import sys
import json
import re
import socket
import smtplib
import subprocess
import traceback
import os

from email.message import EmailMessage

DEFAULT_URL = "https://www.ozone.bg/product/bt-crusher-evochill-grey/"
SENDER = socket.gethostname()
RECIPIENT = ["alex.stoycheva23@gmail.com"]
SUBJECT = "Ozone Skullcrusher Evochill Grey Price Alert"


def send_mail_local(from_addr, to_addrs, subject, body, html=False,
                    sendmail_paths=None, timeout=10):
    """
    Send via local SMTP (localhost:25) or fall back to available sendmail binaries.
    Raises RuntimeError with diagnostic info on failure.
    """
    if isinstance(to_addrs, (list, tuple)):
        to_list = list(to_addrs)
    else:
        to_list = [to_addrs]

    msg = EmailMessage()
    msg["From"] = from_addr or SENDER
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject or SUBJECT
    if html:
        msg.set_content("This message contains HTML. Please view in an HTML-capable client.")
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    # Try connecting to local SMTP (port 25)
    try:
        with smtplib.SMTP("localhost", 25, timeout=timeout) as smtp:
            smtp.send_message(msg)
        return True
    except (ConnectionRefusedError, OSError) as e:
        smtp_err = str(e)

    # Fallback: try common sendmail locations
    if sendmail_paths is None:
        sendmail_paths = ["/usr/sbin/sendmail", "/usr/bin/sendmail", "/sbin/sendmail", "/usr/lib/sendmail"]

    tried = []
    for path in sendmail_paths:
        if not os.path.exists(path) or not os.access(path, os.X_OK):
            tried.append((path, "not found or not executable"))
            continue
        try:
            # -t reads recipients from headers, -i ignore dots alone on lines
            subprocess.run([path, "-t", "-oi"], input=msg.as_bytes(), check=True, timeout=timeout)
            return True
        except subprocess.CalledProcessError as cpe:
            tried.append((path, f"exit {cpe.returncode}"))
        except subprocess.TimeoutExpired:
            tried.append((path, "timeout"))
        except Exception as ex:
            tried.append((path, f"error: {ex}"))

    # No delivery method worked — raise with diagnostics
    diag = {
        "smtp_error": smtp_err,
        "sendmail_tried": tried
    }
    raise RuntimeError(f"Local delivery failed: {diag}")


def fetch_json(url, timeout=10, headers=None):
    headers = headers or {"User-Agent": "python-requests/2.x"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    # try direct JSON response
    try:
        return r.json()
    except ValueError:
        pass
    # try JSON-LD scripts
    ld_json = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', r.text, flags=re.S|re.I)
    if ld_json:
        parsed = []
        for block in ld_json:
            try:
                parsed.append(json.loads(block.strip()))
            except ValueError:
                continue
        return parsed[0] if len(parsed) == 1 else parsed
    raise ValueError("Response is not JSON and no JSON-LD found")

def get_by_path(obj, path):
    if not path:
        return obj
    cur = obj
    parts = re.split(r'\.(?![^\[]*\])', path)  # split on dots not inside brackets
    for p in parts:
        # handle bracket like items[0]
        m = re.match(r'^([^\[\]]+)(?:\[(\d+)\])?$', p)
        if not m:
            raise KeyError(f"Unsupported path segment: {p}")
        key, idx = m.group(1), m.group(2)
        # if current is a list and key is numeric, treat as index
        try:
            if isinstance(cur, list) and key.isdigit():
                cur = cur[int(key)]
            else:
                if isinstance(cur, dict):
                    cur = cur[key]
                else:
                    raise KeyError(key)
            if idx is not None:
                cur = cur[int(idx)]
        except (KeyError, IndexError, TypeError) as e:
            raise KeyError(f"Path not found: {p}") from e
    return cur

def main():
    p = argparse.ArgumentParser(description="Fetch JSON from a URL and extract a path (dot/bracket syntax).")
    p.add_argument("url", nargs="?", help="URL that returns JSON", default=DEFAULT_URL)
    p.add_argument("-p", "--path", help="Dot/bracket path into the JSON (e.g. items[0].name or data.items.0.title)")
    args = p.parse_args()

    try:
        data = fetch_json(args.url)
        if args.path:
            out = get_by_path(data, args.path)
        else:
            out = data
        # pretty-print JSON-compatible output
        print(json.dumps(out, indent=2, ensure_ascii=False))

        send_mail_local(
            from_addr=SENDER,
            to_addrs=RECIPIENT,
            subject=SUBJECT,
            body=f"The current price for {DEFAULT_URL} is: {out} lv.",
            html=False
        )
    except Exception as e:
        traceback.print_exc()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
