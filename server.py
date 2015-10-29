import socket
import time
import re
import sys
from multiprocessing import Process, Manager  #python inbuit libarary which allow to use multiple process concurrently
SERVER_ADDRESS = (HOST, PORT) = '', 8888 
REQUEST_QUEUE_SIZE = 100  #maximum request queue size which sever socket can handle
socket_status = {} # dictionary which wll contain connId as key a socket object as a value
process_status = {} # dictionary which wll contain connId as key a process object as a value
 
 #method which run by each process
def run(connId,timeout,socket_status,time_status,client_connection):
        timeout = int(timeout)
        # taking sleeping time on each second and update corrasponding time_status dictionary 
        while timeout >0:
           time.sleep(1)
           timeout=timeout-1
           time_status[connId]=timeout
        http_response = """\
        {"status":"OK"}
        """
        client_connection.sendall(http_response)
        del time_status[connId]  #Since the time of process is completed delete connId from dictionary 
        client_connection.close() #close the socket
        sys.exit(0) #terminate the process


def serve_forever():
    # socket creation
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    #creation of python process manager which help us to share dictionary among all process
    manager = Manager()
    time_status = manager.dict()
    
    #loop which run continuesly and wait for client to connect
    while True:
        client_connection, client_address = listen_socket.accept()
        request = client_connection.recv(1638467)
        data=request.decode()
        d=data.split(" ")

        """ Check whether request is GET OR PUT.Here i am deciding everthng by 
        getting header  of request & check everything manually."""
        
        if d[0]=='GET':
            if 'connId' in d[1]:
                #Get value of connId & timeout from request
                value_regex = re.compile("(?<=connId=)(?P<value>.*?)(?=&)")
                match = value_regex.search(d[1])
                connId =match.group('value')
                p=d[1].split("&timeout=")
                #Setting key & value in time_status dictionary
                time_status[connId]=p[1]
                # Assigning proces to each connId
                p1 = Process(target=run, args=(connId,p[1],socket_status,time_status,client_connection))
                socket_status[connId]=client_connection
                process_status[connId]=p1
                p1.start()
                
            elif 'api/serverStatus' in d[1]:
                # Creating Response which contain time remaing time of each connection with connection Id
                http_response="{"
                for key,value in time_status.items():
                    http_response=http_response+"'"+str(key)+"':"+"'" +str(value)+"',"
                http_response=http_response+"}"
                client_connection.sendall(http_response)
                client_connection.close() 


        # If request is PUT
        elif d[1]=='/api/kill':
            # Extracting connId from Put request & delete corrasponding socket,process,time
            y= d[7].split(":")
            z=y[1].split("}")
            connId = z[0]
            if time_status.has_key(connId):
                    socket_status[connId].close() #closing socket
                    process_status[connId].terminate() # terminating process corraspond to givn connId
                    del time_status[connId]
                    del socket_status[connId]
                    del process_status[connId] 
                    http_response = """{"status":"kill"}""" 
                    client_connection.sendall(http_response)
                    client_connection.close()
                    
            else: 
                    http_response = """{invaild connection Id :"""+str(connId)+"}"
                    client_connection.sendall(http_response)
                    client_connection.close()
             
        
if __name__ == '__main__':
    serve_forever()
