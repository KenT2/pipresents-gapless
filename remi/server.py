#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import logging
try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
except:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
try:
    import socketserver
except:
    import SocketServer as socketserver
import mimetypes
import webbrowser
import struct
import base64
import hashlib
import sys
import threading
import signal
import time
import os
import re
from threading import Timer
try:
    from urllib import unquote
    from urllib import quote
    from urlparse import urlparse
    from urlparse import parse_qs
except ImportError:
    from urllib.parse import unquote
    from urllib.parse import quote
    from urllib.parse import unquote_to_bytes
    from urllib.parse import urlparse
    from urllib.parse import parse_qs
import cgi

clients = {}
runtimeInstances = []

pyLessThan3 = sys.version_info < (3,)

update_lock = threading.Lock()
update_event = threading.Event()
update_thread = None

log = logging.getLogger('remi.server')


def toWebsocket(data):
    #encoding end deconding utility function
    if pyLessThan3:
        return quote(data)
    return quote(data, encoding='utf-8')

def fromWebsocket(data):
    #encoding end deconding utility function
    if pyLessThan3:
        return unquote(data)
    return unquote(data, encoding='utf-8')


def encodeIfPyGT3(data):
    if not pyLessThan3:
        return data.encode('utf-8')
    return data


def get_method_by(rootNode, idname):
    if idname.isdigit():
        return get_method_by_id(rootNode, idname)
    return get_method_by_name(rootNode, idname)


def get_method_by_name(rootNode, name):
    val = None
    if hasattr(rootNode, name):
        val = getattr(rootNode, name)
    else:
        pass
    return val


def get_method_by_id(rootNode, _id, maxIter=5):
    global runtimeInstances
    for i in runtimeInstances:
        if id(i) == _id:
            return i

    maxIter = maxIter - 1
    if maxIter < 0:
        return None
    _id = int(_id)

    if id(rootNode) == _id:
        return rootNode

    try:
        if hasattr(rootNode, 'children'):
            for i in rootNode.children.values():
                val = get_method_by_id(i, _id)
                if val is not None:
                    return val
    except:
        pass
    return None


def get_instance_key(handler):
    if not handler.server.multiple_instance:
        # overwrite the key value, so all clients will point the same
        # instance
        return 0
    ip = handler.client_address[0]
    unique_port = getattr(handler.server,'websocket_address', handler.server.server_address)[1]
    return ip, unique_port


class ThreadedWebsocketServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, multiple_instance):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)
        self.multiple_instance = multiple_instance


class WebSocketsHandler(socketserver.StreamRequestHandler):
    magic = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    def setup(self):
        global clients
        socketserver.StreamRequestHandler.setup(self)
        log.debug('ws connection established: %r' % (self.client_address,))
        self.handshake_done = False

    def handle(self):
        log.debug('ws handle')
        #on some systems like ROS, the default socket timeout
        #is less than expected, we force it to infinite (None) as default socket value
        self.request.settimeout(None)
        while True:
            if not self.handshake_done:
                self.handshake()
            else:
                if not self.read_next_message():
                    k = get_instance_key(self)
                    clients[k].websockets.remove(self)
                    self.handshake_done = False
                    log.debug('ws ending websocket service')
                    break

    def bytetonum(self,b):
        if pyLessThan3:
            b = ord(b)
        return b

    def read_next_message(self):
        log.debug('ws read_next_message')
        length = self.rfile.read(2)
        try:
            length = self.bytetonum(length[1]) & 127
            if length == 126:
                length = struct.unpack('>H', self.rfile.read(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', self.rfile.read(8))[0]
            masks = [self.bytetonum(byte) for byte in self.rfile.read(4)]
            decoded = ''
            for char in self.rfile.read(length):
                decoded += chr(self.bytetonum(char) ^ masks[len(decoded) % 4])
            self.on_message(fromWebsocket(decoded))
        except Exception as e:
            log.error("Exception parsing websocket", exc_info=True)
            return False
        return True

    def send_message(self, message):
        out = bytearray()
        out.append(129)
        log.debug('send_message')
        length = len(message)
        if length <= 125:
            out.append(length)
        elif length >= 126 and length <= 65535:
            out.append(126)
            out += struct.pack('>H', length)
        else:
            out.append(127)
            out += struct.pack('>Q', length)
        if not pyLessThan3:
            message = message.encode('utf-8')
        out = out + message
        self.request.send(out)

    def handshake(self):
        log.debug('handshake')
        data = self.request.recv(1024).strip()
        log.debug('Handshaking...')
        key = data.decode().split('Sec-WebSocket-Key: ')[1].split('\r\n')[0]
        digest = hashlib.sha1((key.encode("utf-8")+self.magic))
        digest = digest.digest()
        digest = base64.b64encode(digest)
        response = 'HTTP/1.1 101 Switching Protocols\r\n'
        response += 'Upgrade: websocket\r\n'
        response += 'Connection: Upgrade\r\n'
        response += 'Sec-WebSocket-Accept: %s\r\n\r\n' % digest.decode("utf-8")
        self.request.sendall(response.encode("utf-8"))
        self.handshake_done = True

    def on_message(self, message):
        global runtimeInstances
        global update_lock, update_event

        self.send_message('ack')

        with update_lock:
            try:
                # saving the websocket in order to update the client
                k = get_instance_key(self)
                if not self in clients[k].websockets:
                    clients[k].websockets.append(self)
                log.debug('on_message')

                # parsing messages
                chunks = message.split('/')
                if len(chunks) > 3:  # msgtype,widget,function,params
                    # if this is a callback
                    msg_type = 'callback'
                    if chunks[0] == msg_type:
                        widget_id = chunks[1]
                        function_name = chunks[2]
                        params = message[
                            len(msg_type) + len(widget_id) + len(function_name) + 3:]

                        param_dict = parse_parametrs(params)

                        for w in runtimeInstances:
                            if str(id(w)) == widget_id:
                                callback = get_method_by_name(w, function_name)
                                if callback is not None:
                                    callback(**param_dict)
            except Exception as e:
                log.error('error parsing websocket', exc_info=True)

        update_event.set()


def parse_parametrs(p):
    """
    Parses the parameters given from POST or websocket reqs
    expecting the parameters as:  "11|par1='asd'|6|par2=1"
    returns a dict like {par1:'asd',par2:1}
    """
    ret = {}
    while len(p) > 1 and p.count('|') > 0:
        s = p.split('|')
        l = int(s[0])  # length of param field
        if l > 0:
            p = p[len(s[0]) + 1:]
            field_name = p.split('|')[0].split('=')[0]
            field_value = p[len(field_name) + 1:l]
            p = p[l + 1:]
            if field_value.count("'") == 0 and field_value.count('"') == 0:
                try:
                    field_value = int(field_value)
                except ValueError:
                    try:
                        field_value = float(field_value)
                    except ValueError:
                        pass
            ret[field_name] = field_value
    return ret


def gui_update_children_copy(client, leaf):
    """ This function is called when a leaf is updated by gui_updater
        and so, children does not need graphical update, it is only
        required to update the memory copy of the children
    """
    if not hasattr(leaf, 'attributes'):
        return False
    __id = str(id(leaf))
    client.old_runtime_widgets[__id] = leaf.repr(client,False)
    
    for subleaf in leaf.children.values():
        gui_update_children_copy(client, subleaf)
    
    
def gui_updater(client, leaf, no_update_because_new_subchild=False):
    if not hasattr(leaf, 'attributes'):
        return False

    # if there is not a copy of widgets, do it
    if not hasattr(client, 'old_runtime_widgets'):
        client.old_runtime_widgets = dict()  # idWidget,reprWidget

    __id = str(id(leaf))
    # if the widget is not contained in the copy
    if not (__id in client.old_runtime_widgets.keys()):
        client.old_runtime_widgets[__id] = leaf.repr(client,False)
        if not no_update_because_new_subchild:
            no_update_because_new_subchild = True
            # we ensure that the clients have an updated version
            for ws in client.websockets:
                try:
                    # here a new widget is found, but it must be added updating the parent widget
                    if 'parent_widget' in leaf.attributes.keys():
                        parentWidgetId = leaf.attributes['parent_widget']
                        html = get_method_by_id(client.root,parentWidgetId).repr(client)
                        ws.send_message('update_widget,' + parentWidgetId + ',' + toWebsocket(html))
                    else:
                        log.error('the new widget seems to have no parent...')
                    # adding new widget with insert_widget causes glitches, so is preferred to update the parent widget
                    #ws.send_message('insert_widget,' + __id + ',' + parentWidgetId + ',' + repr(leaf))
                except:
                    client.websockets.remove(ws)

    newhtml = leaf.repr(client,False)
    if newhtml != client.old_runtime_widgets[__id]:
        for ws in client.websockets:
            log.debug('update_widget: %s type: %s' %(__id, type(leaf)))
            try:
                html = leaf.repr(client)
                ws.send_message('update_widget,' + __id + ',' + toWebsocket(html))
            except:
                client.websockets.remove(ws)
        #client.old_runtime_widgets[__id] = newhtml
        
        #update children back copy in order to avoid nested updates
        gui_update_children_copy(client, leaf)
        return True
        
    # checking if subwidgets changed
    for subleaf in leaf.children.values():
        gui_updater(client, subleaf, no_update_because_new_subchild)
        
    # widget NOT changed
    return False


class _UpdateThread(threading.Thread):
    def __init__(self, interval):
        threading.Thread.__init__(self)
        self.daemon = True
        self._interval = interval
        Timer(self._interval, self._timed_update).start()
        self.start()

    def _timed_update(self):
        global update_event
        update_event.set()
        Timer(self._interval, self._timed_update).start()

    def run(self):
        while True:
            global clients
            global update_lock, update_event

            update_event.wait()
            with update_lock:
                try:
                    for client in clients.values():
                        if not hasattr(client, 'root'):
                            continue
                        # here we check if the root window has changed
                        if not hasattr(client, 'old_root_window') or client.old_root_window != client.root:
                            # a new window is shown, clean the old_runtime_widgets
                            client.old_runtime_widgets = dict()
                            for ws in client.websockets:
                                try:
                                    html = client.root.repr(client)
                                    ws.send_message('show_window,' + str(id(client.root)) + ',' + toWebsocket(html))
                                except:
                                    client.websockets.remove(ws)
                        client.old_root_window = client.root
                        client.idle()
                        gui_updater(client, client.root)
                except Exception as e:
                    log.error('error updating gui', exc_info=True)

            update_event.clear()


class App(BaseHTTPRequestHandler, object):

    """
    This class will handles any incoming request from the browser
    The main application class can subclass this
    In the do_POST and do_GET methods it is expected to receive requests such as:
        - function calls with parameters
        - file requests
    """
    def __init__(self, request, client_address, server, **app_args):
        self._log = logging.getLogger('remi.server.request')
        self._app_args = app_args
        super(App, self).__init__(request, client_address, server)

    def log_message(self, format_string, *args):
        msg = format_string % args
        self._log.debug("%s %s" % (self.address_string(), msg))

    def log_error(self, format_string, *args):
        msg = format_string % args
        self._log.error("%s %s" % (self.address_string(), msg))

    def instance(self):
        global clients
        global runtimeInstances
        global update_event, update_thread
        """
        This method is used to get the Application instance previously created
        managing on this, it is possible to switch to "single instance for
        multiple clients" or "multiple instance for multiple clients" execution way
        """
        k = get_instance_key(self)
        if not(k in clients.keys()):
            runtimeInstances.append(self)
            clients[k] = self
        wshost, wsport = self.server.websocket_address
        net_interface_ip = self.connection.getsockname()[0]

        websocket_timeout_timer_ms = str(self.server.websocket_timeout_timer_ms)
        pending_messages_queue_length = str(self.server.pending_messages_queue_length)

        # refreshing the script every instance() call, beacuse of different net_interface_ip connections
        # can happens for the same 'k'
        clients[k].script_header = """
<script>
// from http://stackoverflow.com/questions/5515869/string-length-in-bytes-in-javascript
// using UTF8 strings I noticed that the javascript .length of a string returned less 
// characters than they actually were
var pendingSendMessages=[];
function byteLength(str) {
  // returns the byte length of an utf8 string
  var s = str.length;
  for (var i=str.length-1; i>=0; i--) {
    var code = str.charCodeAt(i);
    if (code > 0x7f && code <= 0x7ff) s++;
    else if (code > 0x7ff && code <= 0xffff) s+=2;
    if (code >= 0xDC00 && code <= 0xDFFF) i--; //trail surrogate
  }
  return s;
}

var paramPacketize = function (ps){
    var ret = '';
    for (var pkey in ps) {
        if( ret.length>0 )ret = ret + '|';
        var pstring = pkey+'='+ps[pkey];
        var pstring_length = byteLength(pstring);
        pstring = pstring_length+'|'+pstring;
        ret = ret + pstring;
    }
    return ret;
};

var ws;
function openSocket(){
    try{
        ws = new WebSocket('ws://%s:%s/');
        console.debug('opening websocket');
        ws.onopen = function(evt) {
            if(ws.readyState == 1){
                ws.send('Hello from the client!');
                while(pendingSendMessages.length>0){
                    ws.send(pendingSendMessages.shift()); /*whithout checking ack*/
                }
            }
            else{
                console.debug('onopen fired but the socket readyState was not 1');
            }
        };
        ws.onmessage = websocketOnMessage;
        ws.onclose = websocketOnClose;
        ws.onerror = websocketOnError;
    }catch(ex){ws=false;alert('websocketnot supported or server unreachable');}
}
openSocket();
var comTimeout = null;
function websocketOnMessage (evt){
    var received_msg = evt.data;
    console.debug('Message is received:' + received_msg);
    var s = received_msg.split(',');
    var command = s[0];
    var index = received_msg.indexOf(',')+1;
    received_msg = received_msg.substr(index,received_msg.length-index);/*removing the command from the message*/
    index = received_msg.indexOf(',')+1;
    var content = received_msg.substr(index,received_msg.length-index);
    if( command=='show_window' ){
        document.body.innerHTML = decodeURIComponent(content);
    }else if( command=='update_widget'){
        var elem = document.getElementById(s[1]);
        var index = received_msg.indexOf(',')+1;
        elem.insertAdjacentHTML('afterend',decodeURIComponent(content));
        elem.parentElement.removeChild(elem);
    }else if( command=='insert_widget'){
        if( document.getElementById(s[1])==null ){
            /*the content contains an additional field that we have to remove*/
            index = content.indexOf(',')+1;
            content = content.substr(index,content.length-index);
            var elem = document.getElementById(s[2]);
            elem.innerHTML = elem.innerHTML + decodeURIComponent(content);
        }
    }else if( command=='ack'){
        pendingSendMessages.shift() /*remove the oldest*/
        if(comTimeout!=null)clearTimeout(comTimeout);
    }
    console.debug('command:' + command);
    console.debug('content:' + content);
};
/*this uses websockets*/
var sendCallbackParam = function (widgetID,functionName,params /*a dictionary of name:value*/){
    var paramStr = '';
    if(params!=null) paramStr=paramPacketize(params);
    var message = encodeURIComponent(unescape('callback' + '/' + widgetID+'/'+functionName + '/' + paramStr));
    pendingSendMessages.push(message);
    if( pendingSendMessages.length < %s ){
        ws.send(message);
        if(comTimeout==null)
            comTimeout = setTimeout(checkTimeout, %s);
    }else{
        console.debug('Renewing connection, ws.readyState when trying to send was: ' + ws.readyState)
        renewConnection();
    }
};
/*this uses websockets*/
var sendCallback = function (widgetID,functionName){
    sendCallbackParam(widgetID,functionName,null);
};
function renewConnection(){
    // ws.readyState:
    //A value of 0 indicates that the connection has not yet been established.
    //A value of 1 indicates that the connection is established and communication is possible.
    //A value of 2 indicates that the connection is going through the closing handshake.
    //A value of 3 indicates that the connection has been closed or could not be opened.
    if( ws.readyState == 1){
        try{
            ws.close();
        }catch(err){};
    }
    else if(ws.readyState == 0){
     // Don't do anything, just wait for the connection to be stablished
    }
    else{
        openSocket();
    }
}
function checkTimeout(){
    if(pendingSendMessages.length>0)
        renewConnection();    
}
function websocketOnClose(evt){
    /* websocket is closed. */
    console.debug('Connection is closed... event code: ' + evt.code + ', reason: ' + evt.reason);
    // Some explanation on this error: http://stackoverflow.com/questions/19304157/getting-the-reason-why-websockets-closed
    // In practice, on a unstable network (wifi with a lot of traffic for example) this error appears
    // Got it with Chrome saying:
    // WebSocket connection to 'ws://x.x.x.x:y/' failed: Could not decode a text frame as UTF-8.
    // WebSocket connection to 'ws://x.x.x.x:y/' failed: Invalid frame header
    if(evt.code == 1006){
        renewConnection();
    }

};
function websocketOnError(evt){
    /* websocket is closed. */
    /* alert('Websocket error...');*/
    console.debug('Websocket error... event code: ' + evt.code + ', reason: ' + evt.reason);
};

function uploadFile(widgetID, eventSuccess, eventFail, savePath,file){
    var url = '/';
    var xhr = new XMLHttpRequest();
    var fd = new FormData();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('savepath', savePath);
    xhr.setRequestHeader('filename', file.name);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            /* Every thing ok, file uploaded */
            var params={};params['filename']=file.name;
            sendCallbackParam(widgetID, eventSuccess,params);
            console.log('upload success: ' + file.name);
        }else if(xhr.status == 400){
            var params={};params['filename']=file.name;
            sendCallbackParam(widgetID,eventFail,params);
            console.log('upload failed: ' + file.name);
        }
    };
    fd.append('upload_file', file);
    xhr.send(fd);
};
</script>""" % (net_interface_ip, wsport, pending_messages_queue_length, websocket_timeout_timer_ms)

        # add any app specific headers
        clients[k].html_header = self._app_args.get('html_header', '\n')

        # add client styling
        clients[k].css_header = self._app_args.get('css_header', "<link href='/res/style.css' rel='stylesheet' />\n")

        if not hasattr(clients[k], 'websockets'):
            clients[k].websockets = []

        self.client = clients[k]

        if update_thread is None:
            update_thread = _UpdateThread(self.server.update_interval)

    def idle(self):
        """ Idle function called every UPDATE_INTERVAL before the gui update.
            Usefull to schedule tasks. """
        pass

    def do_POST(self):
        self.instance()
        file_data = None
        try:
            # Parse the form data posted
            savepath = self.headers['savepath']
            filename = self.headers['filename']
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD':'POST',
                        'CONTENT_TYPE':self.headers['Content-Type'],
                        })
            # Echo back information about what was posted in the form
            for field in form.keys():
                field_item = form[field]
                if field_item.filename:
                    # The field contains an uploaded file
                    file_data = field_item.file.read()
                    file_len = len(file_data)
                    log.debug('post: uploaded %s as "%s" (%d bytes)\n' % (field, field_item.filename, file_len))
                else:
                    # Regular form value
                    log.debug('post: %s=%s\n' % (field, form[field].value))

            if file_data is not None:
                log.debug('GUI - server.py do_POST: fileupload path= %s name= %s' % (savepath, filename))
                with open(savepath+filename,'wb') as f:
                    f.write(file_data)
                    self.send_response(200)
        except Exception as e:
            log.error('post error', exc_info=True)
            self.send_response(400)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Protected\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        """Handler for the GET requests."""
        do_process = False
        if self.server.auth is None:
            do_process = True
        else:
            if self.headers.getheader('Authorization') is None:
                log.info("Authenticating")
                self.do_AUTHHEAD()
                self.wfile.write('no auth header received')
            elif self.headers.getheader('Authorization') == 'Basic ' + self.server.auth:
                do_process = True
            else:
                self.do_AUTHHEAD()
                self.wfile.write(self.headers.getheader('Authorization'))
                self.wfile.write('not authenticated')

        if do_process:
            self.instance()
            path = str(unquote(self.path))
            self.process_all(path)

    def process_all(self, function):
        static_file = re.match(r"^/*res\/(.*)$", function)
        attr_call = re.match(r"^\/*(\w+)\/(\w+)\?{0,1}(\w*\={1}\w+\${0,1})*$", function)
        if (function == '/') or (not function):
            # build the root page once if necessary
            should_call_main = not hasattr(self.client, 'root')
            if should_call_main:
                self.client.root = self.main(*self.server.userdata)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(encodeIfPyGT3("<!DOCTYPE html>\n"))
            self.wfile.write(encodeIfPyGT3("<html>\n<head>\n"))
            self.wfile.write(encodeIfPyGT3(
                "<meta content='text/html;charset=utf-8' http-equiv='Content-Type'>\n"
                "<meta content='utf-8' http-equiv='encoding'>\n"))
            self.wfile.write(encodeIfPyGT3(self.client.css_header))
            self.wfile.write(encodeIfPyGT3(self.client.html_header))
            self.wfile.write(encodeIfPyGT3(self.client.script_header))
            self.wfile.write(encodeIfPyGT3("\n</head>\n<body>\n"))
            # render the HTML replacing any local absolute references to the correct IP of this instance
            html = self.client.root.repr(self.client)
            self.wfile.write(encodeIfPyGT3(html))
            self.wfile.write(encodeIfPyGT3("</body>\n</html>"))
        elif static_file:
            static_paths = [os.path.join(os.path.dirname(__file__), 'res')]
            static_paths.extend(self._app_args.get('static_paths', ()))

            filename = None
            found = False
            for s in reversed(static_paths):
                filename = os.path.join(s, static_file.groups()[0])
                if os.path.exists(filename):
                    found = True
                    break

            if not found:
                self.send_response(404)
                return

            mimetype,encoding = mimetypes.guess_type(filename)
            self.send_response(200)
            self.send_header('Content-type', mimetype if mimetype else 'application/octet-stream')
            if self.server.enable_file_cache:
                self.send_header('Cache-Control', 'public, max-age=86400')
            self.end_headers()
            with open(filename, 'rb') as f:
                content = f.read()
                self.wfile.write(content)
        elif attr_call:
            params = list()
            param_dict = parse_qs(urlparse(function).query)
            for k in param_dict:
                params.append(param_dict[k])

            widget,function = attr_call.group(1,2)
            try:
                content,headers = get_method_by(get_method_by(self.client.root, widget), function)(*params)
                if content is None:
                    self.send_response(503)
                    return
                self.send_response(200)
            except IOError:
                log.error('attr call error', exc_info=True)
                self.send_response(404)
                return

            for k in headers.keys():
                self.send_header(k, headers[k])
            self.end_headers()
            self.wfile.write(content)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):

    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, websocket_address,
                 auth, multiple_instance, enable_file_cache, update_interval,
                 websocket_timeout_timer_ms, pending_messages_queue_length, *userdata):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.websocket_address = websocket_address
        self.auth = auth
        self.multiple_instance = multiple_instance
        self.enable_file_cache = enable_file_cache
        self.update_interval = update_interval
        self.websocket_timeout_timer_ms = websocket_timeout_timer_ms
        self.pending_messages_queue_length = pending_messages_queue_length
        self.userdata = userdata


class Server(object):
    def __init__(self, gui_class, start=True, address='127.0.0.1', port=8081, username=None, password=None,
                 multiple_instance=False, enable_file_cache=True, update_interval=0.1, start_browser=True,
                 websocket_timeout_timer_ms=1000, pending_messages_queue_length=1000,
                 userdata=()):
        self._gui = gui_class
        self._wsserver = self._sserver = None
        self._wsth = self._sth = None
        self._address = address
        self._sport = port
        self._multiple_instance = multiple_instance
        self._enable_file_cache = enable_file_cache
        self._update_interval = update_interval
        self._start_browser = start_browser
        self._websocket_timeout_timer_ms = websocket_timeout_timer_ms
        self._pending_messages_queue_length = pending_messages_queue_length
        if username and password:
            self._auth = base64.b64encode("%s:%s" % (username,password))
        else:
            self._auth = None

        if not isinstance(userdata, tuple):
            raise ValueError('userdata must be a tuple')

        if start:
            self.start(*userdata)

    def start(self, *userdata):
        # here the websocket is started on an ephemereal port
        self._wsserver = ThreadedWebsocketServer((self._address, 0), WebSocketsHandler, self._multiple_instance)
        wshost, wsport = self._wsserver.socket.getsockname()[:2]
        log.info('Started websocket server %s:%s' % (wshost, wsport))
        self._wsth = threading.Thread(target=self._wsserver.serve_forever)
        self._wsth.daemon = True
        self._wsth.start()

        # Create a web server and define the handler to manage the incoming
        # request
        self._sserver = ThreadedHTTPServer((self._address, self._sport), self._gui,
                                           (wshost, wsport), self._auth,
                                           self._multiple_instance, self._enable_file_cache,
                                           self._update_interval, self._websocket_timeout_timer_ms,
                                           self._pending_messages_queue_length, *userdata)
        shost, sport = self._sserver.socket.getsockname()[:2]
        # when listening on multiple net interfaces the browsers connects to localhost
        if shost == '0.0.0.0':
            shost = '127.0.0.1'
        base_address = 'http://%s:%s/' % (shost,sport)
        log.info('Started httpserver %s' % base_address)
        if self._start_browser:
            try:
                import android
                android.webbrowser.open(base_address)
            except:
                # use default browser instead of always forcing IE on Windows
                if os.name == 'nt':
                    webbrowser.get('windows-default').open(base_address)
                else:
                    webbrowser.open(base_address)
        self._sth = threading.Thread(target=self._sserver.serve_forever)
        self._sth.daemon = True
        self._sth.start()

    def serve_forever(self):
        # we could join on the threads, but join blocks all interupts (including
        # ctrl+c, so just spin here
        try:
            while True:
                signal.pause()
        except Exception:
            # signal.pause() is missing for Windows; wait 1ms and loop instead
            while True:
                time.sleep(1)

    def stop(self):
        self._wsserver.shutdown()
        self._wsth.join()
        self._sserver.shutdown()
        self._sth.join()


def start(mainGuiClass, **kwargs):
    """This method starts the webserver with a specific App subclass."""
    try:
        debug = kwargs.pop('debug')
    except KeyError:
        debug = False
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    s = Server(mainGuiClass, start=True, **kwargs)
    s.serve_forever()

