import os,sys,thread,socket,ssl

MAX_QUEUE = 20          # Max number of connection
MAX_PKT_SIZE = 99999     # Max size of packet

def gen_cert(name):
    cmd = 'cd cert-master && sh _make_site.sh '+ name
    os.system(cmd)

def main():
    
    # Usage  : python ssl_web_proxy.py
    # Setting: set https proxy with localhost and port number 4433

    port = 4433
    host = ''

    try:
        # create socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind host and port
        s.bind((host, port))

        # listenning
        s.listen(MAX_QUEUE)
    
    except socket.error, (value, message):
        if s:
            s.close()
        print "Fail to open socket"
        sys.exit(1)

    # connect with web client 
    while 1:
        conn, client_addr = s.accept()

        # thread to handle web client and end server
        thread.start_new_thread(proxy_thread, (conn, client_addr))
        
    s.close()

def proxy_thread(conn, client_addr):

    # get request from web browser
    request = conn.recv(MAX_PKT_SIZE)
    
    #Find CONNECT method and parsing 
    if request.find('CONNECT'):
	# split first line 
	line = request.split('\n')[0]
	# get url
	url = line.split(' ')[1]
	# find the webserver and port
	http_pos = url.find("://")          # find pos of ://
	if (http_pos==-1):
	    temp = url
	else:
	    temp = url[(http_pos+3):]       # get the rest of url
	# find / in url and remove it
	webserver_pos = temp.find("/")
	if webserver_pos == -1:
	    webserver_pos = len(temp)
	
	# host 
	webserver = temp[:webserver_pos]
	
	# generate certification
	gen_cert(webserver)

	try:
	    # create a socket to connect to the end server
	    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    # connect end server with port 80
	    s.connect((webserver, 80))
	    # put dummy behind of request
	    dummyRequest = 'GET / HTTP/1.1\r\nHost: test.gilgil.net\r\n\r\n'
	    request= dummyRequest + request
	    # send request to end server
	    s.send(request)         
	    
	    while 1:
		# receive data from end server
		data = s.recv(MAX_PKT_SIZE)
		#print data
		# if 404 data, ignore it
		if data.find('HTTP/1.1 404 Not Found') >= 0:
		    continue
		if (len(data) > 0):
		    # send to browser
		    conn.send(data)
		else:
		    break
		s.close()
		conn.close()
	except socket.error, (value, message):
	    s.close()
	    conn.close()
	    sys.exit(1)

    
if __name__ == '__main__':
    main()
