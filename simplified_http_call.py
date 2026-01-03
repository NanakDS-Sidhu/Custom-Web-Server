import socket 

#create a connection to port
s=socket.create_connection(("127.0.0.1",8000))

#send a get request to the server
s.sendall(b"GET / HTTP/1.1\r\nHOST:localhost\r\n\r\n")

#recieve upto 1024 bits of the response
print(s.recv(1024).decode())
s.close()

#use to test the server 