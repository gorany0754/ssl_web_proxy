import os,sys,thread,socket,ssl

MAX_QUEUE = 20          # Max number of connection
MAX_PKT_SIZE = 99999     # Max size of packet

# Gorany's SSL proxy
# Usage :   web browser 


def gen_cert(webserver):
    # generate cert
    cmd = 'cd cert-master && sh _make_site.sh '+ webserver
    os.system(cmd)

def init_cert():
    # initialize cert
    cmd = 'cd cert-master && sh _init_site.sh '
    os.system(cmd)

def main():
    
    port = 4433
    host = ''

    init_cert()

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(MAX_QUEUE)
    
    except socket.error, (value, message):
        if s:
            s.close()
        print "Fail to open socket"
        sys.exit(1)

    while 1:
        conn, client_addr = s.accept()
        thread.start_new_thread(proxy_thread, (conn, client_addr))
        
    s.close()

def proxy_thread(conn, client_addr):

    # get request from web browser
    request = conn.recv(MAX_PKT_SIZE)
    
    #Find CONNECT method and parse it
    if request.find('CONNECT'):
	line = request.split('\n')[0]
	url = line.split(' ')[1]
	http_pos = url.find("://")          # find pos of ://
	if (http_pos==-1):
	    temp = url
	else:
	    temp = url[(http_pos+3):]       # get the rest of url
	webserver_pos = temp.find("/")
	if webserver_pos == -1:
	    webserver_pos = len(temp)
	
	# host 
	webserver = temp[:webserver_pos]
	
	# Answer for connection request
	conn.send('HTTP/1.1 Connection established\r\n\r\n')

	# generate certification
	gen_cert(webserver)
	
	# define certification dir	
	cert_dir= os.getcwd() +'/cert-master/'+ webserver + '.pem'
	
	# wrapping conn socket as ssl with cert
	ssl_conn= ssl.wrap_socket(conn, server_side =True, keyfile = cert_dir, certfile = cert_dir)
	
	#receive ssl request
	ssl_request = ssl_conn.recv(MAX_PKT_SIZE)

	try:
	    # create a ssl socket
	    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    ssl_s = ssl.wrap_socket(s)
	    # connect end server with port 443
	    ssl_s.connect((webserver, 443))

	    # send request to end server
	    ssl_s.send(ssl_request)         
	    
	    while 1:
		# receive data from end server
		data = ssl_s.recv(MAX_PKT_SIZE)
		if (len(data) > 0):
		    # send to browser
		    ssl_conn.send(data)
		else:
		    break
		ssl_s.close()
		ssl_conn.close()
	except socket.error, (value, message):
	    ssl_s.close()
	    ssl_conn.close()
	    sys.exit(1)

if __name__ == '__main__':
    main()
