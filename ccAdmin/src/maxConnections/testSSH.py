import sys
import paramiko
import time
import re



def getRouterDialPeers(ip,user,password):
    try:
        # Define SSH parameters

        username = user

        # Logging into device
        session = paramiko.SSHClient()

        session.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        session.connect(ip, port=22, username=user, password=password, look_for_keys=False)
        #stdin, stdout, stderr = client.exec_command("show running-config dial-peer")


        connection = session.invoke_shell()

        # Setting terminal length for entire output - no pagination
        connection.send("terminal length 0\n")
        time.sleep(1)
        # output0 = connection.recv(65535)

        # Entering global config mode

        comando = "show running-config dial-peer " + " \n"
        connection.send("\n")
        connection.send(comando)
        time.sleep(0.5)

        # Checking command output for IOS syntax errors
        output1 = connection.recv(65535)



        if re.search(r"% Invalid input detected at", output1):
            config = "* There was at least one IOS syntax error on device %s" % ip
        else:
            config = output1
        # Test for reading command output
        # print output + "\n"

        # Closing the connection
        session.close()

        print("Recibi la config ****************** " + config)

        return config

    except paramiko.AuthenticationException:
        print "* Invalid username or password. \n* Please check the username/password file or the device configuration!"
        print "* Closing program...\n"

def setDialPeerMaxCon(ip, user, password,DialPeer,MaxCon):
    try:
        # Define SSH parameters

        username = user

        # Logging into device
        session = paramiko.SSHClient()

        session.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        session.connect(ip, port=22, username=user, password=password, look_for_keys=False)
        #stdin, stdout, stderr = client.exec_command("show running-config dial-peer")


        connection = session.invoke_shell()

        # Setting terminal length for entire output - no pagination
        connection.send("terminal length 0\n")
        time.sleep(1)
        # output0 = connection.recv(65535)

        # Entering global config mode

        comando = "config term " + " \n"
        connection.send("\n")
        connection.send(comando)
        time.sleep(0.5)

        # Checking command output for IOS syntax errors
        output1 = connection.recv(65535)

        comando = "dial-peer voice " + DialPeer+ " voip " + " \n" + "max-conn " + MaxCon + " \n"
        connection.send("\n")
        connection.send(comando)
        time.sleep(0.5)

        # Checking command output for IOS syntax errors
        output1 = connection.recv(65535)



        if re.search(r"% Invalid input detected at", output1):
            config = "* There was at least one IOS syntax error on device %s" % ip
        else:
            config = output1
        # Test for reading command output
        # print output + "\n"

        comando = "exit"  + " \n" + "exit " + " \n"+ "wr mem" + " \n"
        connection.send("\n")
        connection.send(comando)
        time.sleep(0.5)

        # Checking command output for IOS syntax errors
        output1 = connection.recv(65535)



        # Closing the connection
        session.close()

        print("aplique cambio")

        return config

    except paramiko.AuthenticationException:
        print "* Invalid username or password. \n* Please check the username/password file or the device configuration!"
        print "* Closing program...\n"



def simpleSSH():
    hostname="192.168.0.3"
    user="cisco"
    password="cisco"

    port=22

    try:
        client = paramiko.SSHClient()
        #client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname, port=port, username=user, password=password, look_for_keys=False)
        stdin, stdout, stderr = client.exec_command("show running-config dial-peer")


        print stdout.read()

    finally:
        client.close()

if __name__ == '__main__':

    #config = getRouterDialPeers("192.168.0.2","cisco","cisco")
    #salida = setDialPeerMaxCon("192.168.0.2","cisco","cisco", "119", "10")
    simpleSSH()


