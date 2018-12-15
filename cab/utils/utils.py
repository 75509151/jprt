import magic

def get_mimetype(file_name):
    mime = magic.Magic(mime=True)
    return mime.from_file(file_name)

