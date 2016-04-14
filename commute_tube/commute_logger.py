import logging, re
from subprocess import CalledProcessError

try:
    import codecs
except ImportError:
    codecs = None
try:
    unicode
    _unicode = True
except NameError:
    _unicode = False

class CommuteTubeLoggingHandler(logging.FileHandler):

    def __init__(self, filename, mode="w", encoding=None, delay=0):
        """
        Use the specified filename for streamed logging
        """
        if codecs is None:
            encoding = None
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)
        self.mode = mode
        self.encoding = encoding
        self.downloadInProgress = False

        header = """<html>
        <style type="text/css">
        .downloadprocess {
            height: 15px;
            background-color: #efefef;
            overflow: hidden;
            }

        pre {
            display: inline;
        }

        body {
            font-family: monospace;
        }

        .DEBUG {
            opacity: 0.5;
        }

        .ERROR {
            opacity: 0.5;
            color:red;
        }

        .WARNING {
            opacity: 0.5;
            color:orange;
        }

        .youtubedl {
        }
        </style>

        <head></head>\n"""

        self.stream.write(header)

    def emit(self, record):

        prefix = ""

        message = str(record.msg)

        #TODO Download does not match on every system
        if ("[download]" in message and not self.downloadInProgress):
            prefix = "<div class='downloadprocess'>"
            self.downloadInProgress = True
        elif (self.downloadInProgress and not "[download]" in message):
            prefix = "</div>"
            self.downloadInProgress = False

        classes = []
        classes.append(record.levelname)
        classes.append(record.module)

        if (isinstance(record.msg, CalledProcessError)):
            classes.append("exception")

        try:
            formattedMessage = re.sub(r'\b((http|https)://[a-zA-Z0-9./?=_-]*)\b', r'<a href="\1">\1</a>', message)
        except:
            formattedMessage = message

        record.msg = "\t\t\t"+prefix+"<div class='" + " ".join(classes) + "'> \
        <span class='timestamp'>"+record.asctime+"</span> \
        <span class='module'>"+record.module+"</span> \
        <span class='loglevel'>"+record.levelname+"</span> \
        <span class='message'>" + formattedMessage + "</span></div>"

        #TODO Exceptions are printed afterwards to the file with this call
        logging.FileHandler.emit(self, record)

    def end():
        #TODO This needs to be called from commute tube at the end
        self.stream.write("\t<body>\n</html>")
