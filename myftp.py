import socket
import getpass
import random
class FTPClient:
    def __init__(self):
        self.connection = False
        self.useable = False

    def send_command(self, cmd):
        self.clientSocket.sendall(f"{cmd}\r\n".encode('utf-8'))
        resp = self.clientSocket.recv(1024)
        return resp.decode()
        
    def set_transfer_type(self, type):
        if not hasattr(self,'clientSocket') or self.connection == False:
            print("Not connected.")
            return
        if type.lower() == 'ascii':
            cmd = "TYPE A"
        elif type.lower() == 'binary':
            cmd = "TYPE I"
        print(self.send_command(f"{cmd}"),end="")

    def quit(self):
        if not hasattr(self,'clientSocket') or self.connection == False:
            return
        
        print(self.send_command("QUIT"),end="")
        self.connection = False
        self.useable = False
        self.clientSocket.close()

    def cd(self,path=None):
        if not hasattr(self,'clientSocket') or self.connection == False:
            print("Not connected.")
            return
        
        if path is None :
            path = input("Remote directory ")
        print(self.send_command(f"CWD {path}"),end="")

    def close(self):
        self.disconnect()

    def delete(self,file=None):
        if not hasattr(self,'clientSocket') or self.connection == False:
            print("Not connected.")
            return
        
        if file is None:
            file = input('Remote file ')
        print(self.send_command(f'DELE {file}'),end="")

    def disconnect(self):
        if not hasattr(self,'clientSocket') or self.connection == False:
            print("Not connected.")
            return
        
        print(self.send_command("QUIT"),end="")

        self.connection = False
        self.useable = False
        self.clientSocket.close()

    def get(self, remote_file, local_file=None):
        if not hasattr(self, 'clientSocket') or self.connection == False:
            print("Not connected.")
            return
        
        num = random.randint(0,65535)
        ipaddr = socket.gethostbyname(socket.gethostname())+f".{num//256}.{num%256}"
        ipaddr = ipaddr.replace('.',',')
        
        resp = self.send_command(f'PORT {ipaddr}')
        print(resp,end='')

        self.clientSocket.sendall(b'PASV\r\n')
        pasv_response = self.clientSocket.recv(1024).decode()
        data_host, data_port = self.parse_pasv_response(pasv_response)
        
        resp = self.send_command(f'RETR {remote_file}')
        print(resp,end='')

        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.settimeout(10)
        data_socket.connect((data_host, data_port))

        with open(local_file, 'wb') as lf:
            while True:
                try:
                    data = data_socket.recv(1024)
                    if not data:
                        break
                    lf.write(data)
                except socket.timeout:
                    print("Data connection timed out.")
                    break
                except Exception as e:
                    print("An error occurred:", e)
                    break
        data_socket.close()
        resp = self.clientSocket.recv(1024).decode()
        print(resp,end='')

    def parse_pasv_response(self,resp):
        parts = resp.split('(')[1].split(')')[0].split(',')
        host = '.'.join(parts[:4])
        port = int(parts[4])*256 + int(parts[5])
        return host, port
    
    def ls(self,file=''):
        if not hasattr(self, 'clientSocket') or not self.connection:
            print("Not connected.")
            return
        num = random.randint(0,65535)
        ipaddr = socket.gethostbyname(socket.gethostname())+f".{num//256}.{num
                                                                           %256}"
        ipaddr = ipaddr.replace('.',',')
        
        resp = self.send_command(f'PORT {ipaddr}')

        print(resp, end='')
        
        data_host, data_port = self.parse_pasv_response(self.send_command('PASV'))
        with socket.create_connection((data_host, data_port)) as data_socket:
            dir_response = self.send_command(f'NLST {file}')
            if dir_response.startswith('5'):
                return
            while True:
                data = data_socket.recv(4096)
                if not data:
                    break
                print(data.decode(), end='')
        control_response = self.clientSocket.recv(1024).decode()
        print(control_response, end='')

    def open(self,host,port=21):
        if (hasattr(self, 'clientSocket') and self.connection) or self.useable:
            print(f"Already connected to {self.name}, use disconnect first.")
            return
        if host == '':
            print("Usage: open host name [port]")
            return
        print(f'Connected to {host}.')
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket.connect((host,int(port)))
        self.clientSocket.settimeout(1)
        self.name = host
        resp = self.clientSocket.recv(1024)
        print(resp.decode(),end="")
        print(self.send_command('OPTS UTF8 ON'),end="")
        self.useable = True
        user = input(f'User ({host}:(none)): ')
        print(self.send_command(f'USER {user}'),end="")
        if resp.decode().startswith('5'):
            print('Login failed.')
            return
        password = getpass.getpass("Password: ")
        print(self.send_command(f'PASS {password}'),end="")
        if resp.decode().startswith('5'):
            print('Login failed.')
            return
        else:
            self.connection = True
        self.username = user
        self.password = password

    def put(self, local_file=None,remote_file=None):
        if not hasattr(self, 'clientSocket') or not self.connection:
            print("Not connected.")
            return
        if local_file is None and remote_file is None:
            local_file = input('Local file ')
            remote_file = input('Remote file ')
        number = random.randint(0,65535)
        ipaddr = socket.gethostbyname(socket.gethostname())+f".{number//256}.{number%256}"
        ipaddr = ipaddr.replace('.',',')
        self.clientSocket.send(f'PORT {ipaddr}\r\n'.encode())
        port_status = self.clientSocket.recv(1024)
        print(port_status.decode(),end="")
        with open(local_file,'rb') as f:
            try:

                self.clientSocket.sendall(b'PASV\r\n')
                resp = self.clientSocket.recv(1024).decode()
                port_start = resp.find('(') + 1
                port_end = resp.find(')')
                port_str = resp[port_start:port_end].split(',')
                data_port = int(port_str[-2]) * 256 + int(port_str[-1])
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.connect((socket.gethostbyname(self.name), data_port))
                self.clientSocket.sendall((f'STOR {remote_file}\r\n').encode())
                resp = self.clientSocket.recv(4096).decode()
                print(resp,end='')
                if not resp.startswith('150'):
                    return
                data = f.read(4096)
                while data:
                    data_socket.sendall(data)
                    data = f.read(4096)
            finally:
                data_socket.close()
            resp = self.clientSocket.recv(1024)
            print(resp.decode(),end='')

    def pwd(self):
        if not hasattr(self,'clientSocket') or self.connection == False:
            print("Not connected.")
            return
        print(self.send_command('PWD'), end="")

    def rename(self,file_name=None,new_name=None):
        if not hasattr(self,'clientSocket') or self.connection == False:
            print("Not connected.")
            return
        if file_name is None:
            file_name = input('From name ')
        if file_name == '':
            print('rename from-name to-name.')
            return
        if new_name is None:
            new_name = input('To name ')
        if new_name == '':
            print('rename from-name to-name.')
            return
        
        resp = self.send_command(f'RNFR {file_name}')
        print(resp,end="") 
        if not resp.startswith('350') or resp.startswith('5'):
            return
        
        print(self.send_command(f'RNTO {new_name}'),end="") 

    def user(self,name=None,password=None):
        if not hasattr(self,'clientSocket') or self.useable == False:
            print("Not connected.")
            return
        if name is None:
            name = input('Username ')
        resp = self.send_command(f'User {name}')

        print(resp,end="")

        if not resp.startswith('331'):
            print('Login failed.')
            return
        if password is None:
            password = getpass.getpass("Password: ")
        
        resp = self.send_command(f'PASS {password}')
        if resp.startswith('5'):
            print('Login failed.')
            return
        else:
            self.connection = True
        self.username = name
        self.password = password
        print(resp,end="")

def main():
    ftp = FTPClient()
    while True:
        line = input("ftp> ").strip()
        if not line:
            continue
        cmd = line.split()
        command = cmd[0]

        if command == 'quit' or command == 'bye':
            ftp.quit()
            break
        elif command == 'open':
            if len(cmd) == 1:
                host = input("To ")
                ftp.open(host)
            elif len(cmd) == 2:
                ftp.open(cmd[1])
            elif len(cmd) == 3:
                ftp.open(cmd[1],cmd[2])
            else :
                print('Usage: open host name [port]')

        elif command == 'ascii' or command == 'binary':
            ftp.set_transfer_type(command)

        elif command == 'cd':
            if len(cmd)>1:
                ftp.cd(cmd[1])
            else:
                ftp.cd()

        elif command == 'close':
            ftp.close()

        elif command == 'delete':
            if len(cmd) == 1:
                ftp.delete()
            else :
                ftp.delete(cmd[1])

        elif command == 'disconnect':
            ftp.disconnect()

        elif command == 'get':
            if len(cmd)==1:
                remote = input('Remote file ')
                if remote == '':
                    print('Remote file get [ local-file ].')
                    continue
                local = input('Local file ')
                ftp.get(remote,local)
            elif len(cmd)==2:
                ftp.get(cmd[1],cmd[1])
            elif len(cmd) >=3:
                ftp.get(cmd[1],cmd[2])

        elif command == 'ls':
            if len(cmd) == 1:
                ftp.ls()
            else:
                ftp.ls(cmd[1])

        elif command == 'put':
            if len(cmd) == 1:
                ftp.put()
            elif len(cmd) == 2:
                ftp.put(cmd[1],cmd[1])
            else :
                ftp.put(cmd[1],cmd[2])

        elif command == 'pwd':
            ftp.pwd()

        elif command == 'rename':
            if len(cmd) == 1:
                ftp.rename()
            elif len(cmd) == 2:
                ftp.rename(cmd[1])
            else :
                ftp.rename(cmd[1], cmd[2])

        elif command == 'user':
            if len(cmd) == 1:
                ftp.user()
            elif len(cmd) == 2:
                ftp.user(cmd[1])
            elif len(cmd) ==3 :
                ftp.user(cmd[1], cmd[2])
            elif len(cmd) > 4 :
                print('Usage: user username [password] [account]')
        else:
            print("Invalid command.")


if  __name__ == '__main__':
    main()