import logging, re

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

        .WARN {
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

        if ("[K[download]" in record.msg and not self.downloadInProgress):
            prefix = "<div class='downloadprocess'>"
            self.downloadInProgress = True
        elif (self.downloadInProgress and not "[K[download]" in record.msg):
            prefix = "</div>"
            self.downloadInProgress = False

        formattedMessage = re.sub(r'\b((http|https)://[a-zA-Z0-9./?=_-]*)\b', r'<a href="\1">\1</a>', record.msg)

        record.msg = "\t\t\t"+prefix+"<div class='"+record.levelname+" "+record.module+"'> \
        <span class='timestamp'>"+record.asctime+"</span> \
        <span class='module'>"+record.module+"</span> \
        <span class='loglevel'>"+record.levelname+"</span> \
        <span class='message'>" + formattedMessage + "</span></div>"

        logging.FileHandler.emit(self, record)

    def end():
        #TODO This needs to be called from commute tube at the end
        self.stream.write("</html>")
