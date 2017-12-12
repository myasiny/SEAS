import socket

def check_connection(img, dt):
    try:
        socket.create_connection((socket.gethostbyname("www.google.com"), 80), 2)
        img.source = "img/ico_connection_success.png"
    except:
        img.source = "img/ico_connection_fail.png"
    finally:
        img.reload()