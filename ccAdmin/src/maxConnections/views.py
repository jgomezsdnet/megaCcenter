import sys
import paramiko
import time
import re
from django.shortcuts import render, redirect
from django.http import HttpResponse
from models import Master, Cubes, City
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail


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

        #print("Recibi la config ****************** " + config)
        print("Recibi la config ****************** ")

        return config

    except paramiko.AuthenticationException:
        print "* Invalid username or password. \n* Please check the username/password file or the device configuration!"
        print "* Closing program...\n"


def checkUserAuth(user):
    if user.is_authenticated():
        return True
    else:
        return False

def index(request):
    #master = Master.objects.all()
    #primer = Master.objects.all()[0].cityName

    if request.method== 'POST':
        usrname=request.POST['username']
        passwd=request.POST['password']
        print("recibi login de= " + usrname + " con pwd= " + passwd)
        user=authenticate(username=usrname, password=passwd)
        if user is not None:
            print("login good")
            login(request,user)
            return render(request, "index.html", {'user': user, 'citySelected': None, 'mensajeSalida':None})

        print("login failed")
        return render(request, "index.html", {'user': user, 'citySelected': None, 'mensajeSalida':"Login Failed"})

    user=checkUserAuth(request.user)
    if(user==False):
        user= None
    return render(request, "index.html",{'user':user,'citySelected':None, 'mensajeSalida':None})


def updateCityInfo(cityName, maxConn):

    busqueda = City.objects.filter(CityName=cityName)
    newCity = busqueda[0]
    newConn= newCity.ActualMaxConn + maxConn
    newCity.ActualMaxConn = newConn
    print("update city=" + newCity.CityName + " newConn= " + str(newCity.ActualMaxConn))
    newCity.save()


def setCityInfo(master, cityName, maxConn, DialPeer):

    try:
        busqueda = City.objects.filter(CityName=cityName)
        newCity = busqueda[0]
        newCity.ActualMaxConn = maxConn
        newCity.DialPeer = DialPeer
        newCity.save()

    except:
        newCity = City()
        newCity.CityName = cityName
        newCity.idMaster = master
        newCity.ActualMaxConn = maxConn
        newCity.DialPeer = DialPeer
        newCity.save()

    return newCity



def getConfigSSH(Cube,master,update):
    mensaje=""

    config=getRouterDialPeers(Cube.ip, Cube.usr, Cube.pwd)
    description = "description ***Inbound WAN From SIP PSTN - "
    busquedaDialPeer = "dial-peer voice "
    maxConDesc = "max-conn "
    dialPeer = 0
    lastLine = ""
    ciudad=""


    lineas = config.split('\n');
    for line in lineas:
        if (line.startswith(busquedaDialPeer)):
            subLineDP = line[len(busquedaDialPeer):len(line)]
            indexDialPeer = subLineDP.rfind(" ")
            subLineDP = subLineDP[0:indexDialPeer]
            #subLineDP = subLineDP.replace(" ", "")
            dialPeer =int(float(subLineDP))
            #print("Enconte Dial Peer= "+ subLineDP)
            ciudad=""


        else:
            index = line.rfind(description)
            if (index>0):
                subLine=line[len(description):len(line)]
                index= subLine.rfind(" ")
                subLine=subLine[0:index]
                subLine=subLine.replace("***","")
                #subLine = subLine.replace(" ", "")

                ciudad=subLine;

                if (len(ciudad) < 2):
                    ciudad=""

                #print("encontre ciudad= " +ciudad )
            else:

                index = line.rfind(maxConDesc)
                #if (line.startswith(maxConDesc)):
                if(index>0):
                    maxCon = line[len(maxConDesc):len(line)]
                    maxCon = maxCon.replace(" ", "")
                    maxCon = int(maxCon)

                    if (len(ciudad) > 2):
                        if (update==0):
                            newCity= setCityInfo(master, ciudad, maxCon, dialPeer)
                        else:
                            updateCityInfo(ciudad,maxCon)

                        mensaje = mensaje + " " + ciudad + str(update)+ " con maxLineas " + str(maxCon) + " "

                        print ("encontre: " + " " + ciudad + str(update)+ " con maxLineas " + str(maxCon) + " ")

    return "mensaje"



def getConfig(Cube,master,update):

    file= "maxConnections/sample/"+Cube.CubeName+".config"
    mensaje= ""
    f = open(file, 'r')
    description= "description ***Inbound WAN From SIP PSTN - "
    busquedaDialPeer= "dial-peer voice "
    maxConDesc="max-conn "
    dialPeer=0
    lastLine=""
    line=f.readline()
    while (line):


        if (line.startswith(busquedaDialPeer)):
            subLineDP = line[len(busquedaDialPeer):len(line)]
            indexDialPeer = subLineDP.rfind(" ")
            subLineDP = subLineDP[0:indexDialPeer]
            #subLineDP = subLineDP.replace(" ", "")
            dialPeer =int(float(subLineDP))
            #print("Enconte Dial Peer= "+ subLineDP)



        index = line.rfind(description)
        if (index>0):
            subLine=line[len(description):len(line)]
            index= subLine.rfind(" ")
            subLine=subLine[0:index]
            subLine=subLine.replace("***","")
            #subLine = subLine.replace(" ", "")

            ciudad=subLine;
            #print("encontre ciudad= " +ciudad )
            if (len(ciudad)>2):
                line = f.readline()
                line = f.readline()


                index = line.rfind(maxConDesc)
                maxCon = line[len(maxConDesc):len(line)]
                maxCon = maxCon.replace(" ", "")
                maxCon = int(maxCon)

                if (update==0):
                    newCity= setCityInfo(master, ciudad, maxCon, dialPeer)
                else:
                    updateCityInfo(ciudad,maxCon)

                mensaje = mensaje + " " + ciudad + str(update)+ " con maxLineas " + str(maxCon) + " "
        line = f.readline()

    f.close()
    return mensaje


def getCitiesInfoAll(request):
    busqueda = City.objects.all()

    for city in busqueda:
        print (city.CityName +"lineas= " + str(city.ActualMaxConn))

    return HttpResponse("done= " + str(len(busqueda)))


def getCities(cityName):
    busqueda = Master.objects.filter(cityName=cityName)
    master=busqueda[0]
    mensaje="nada"

    busqueda = Cubes.objects.filter(idMaster=master)

    if cityName=="Guadalajara":
        mensaje=getConfigSSH(busqueda[0],master,0)
    #else:
    #    mensaje = getConfig(busqueda[0],master,0)

    if cityName=="Guadalajara":
        mensaje=getConfigSSH(busqueda[1],master,1)
    #else:
    #    mensaje = getConfig(busqueda[1],master,1)

    return mensaje

    return "cube encontrado1= " + busqueda[0].CubeName + "  Encontrado2" + busqueda[1].CubeName

def getCityInfo(request):

    mensaje = getCities("Guadalajara")

    mensaje = mensaje + "  " + getCities("Puebla")
    mensaje = mensaje + "  " + getCities("Culiacan")

    return HttpResponse(mensaje)



def init(request):

    mensaje=""
    try:
        busqueda = Master.objects.filter(cityName="Guadalajara")
        idGdl = busqueda[0].id
        mensaje=" Gdl ya existe=   "
        unMaster=busqueda[0]
    except:
        unMaster = Master()
        unMaster.cityName = "Guadalajara"
        unMaster.numTrunks = 300
        unMaster.save()
        idGdl = unMaster.id
        mensaje= " Gdl Insertado  "

    mensaje1= mensaje + str(idGdl)

    try:
        busqueda = Cubes.objects.filter(CubeName="GDL01")
        idGdl01 = busqueda[0].id
        mensaje = " Cube GDL01 YA EXISTE   "
    except:
        unCube = Cubes()
        unCube.CubeName="GDL01"
        unCube.idMaster = unMaster
        unCube.ip="192.168.0.2"
        unCube.usr="cisco"
        unCube.pwd="cisco"
        unCube.save()
        idGdl01 = unCube.id
        mensaje = " GDL01 Insertado   "


    mensaje4 = mensaje + str(idGdl01)


    try:
        busqueda = Cubes.objects.filter(CubeName="GDL02")
        idGdl02 = busqueda[0].id
        mensaje = " Cube GDL02 YA EXISTE   "
    except:
        unCube = Cubes()
        unCube.CubeName="GDL02"
        unCube.idMaster = unMaster
        unCube.ip="192.168.0.3"
        unCube.usr = "cisco"
        unCube.pwd = "cisco"
        unCube.save()
        idGdl02 = unCube.id
        mensaje = " GDL02 Insertado   "


    mensaje5 = mensaje + str(idGdl02)

    try:
        busqueda = Master.objects.filter(cityName="Puebla")
        idPue = busqueda[0].id
        mensaje = "  Pue ya existe= "
        unMaster = busqueda[0]
    except:
        unMaster = Master()
        unMaster.cityName = "Puebla"
        unMaster.numTrunks = 200
        unMaster.save()
        idPue = unMaster.id
        mensaje = " PUE Insertado   "

    mensaje2 = mensaje + str(idPue)


    try:
        busqueda = Cubes.objects.filter(CubeName="PUE01")
        idPue01 = busqueda[0].id
        mensaje = " Cube PUE01 YA EXISTE   "
    except:
        unCube = Cubes()
        unCube.CubeName="PUE01"
        unCube.idMaster = unMaster
        unCube.ip="3.3.3.3"
        unCube.usr="usrpue01"
        unCube.pwd="pwdpue01"
        unCube.save()
        idPue01 = unCube.id
        mensaje = " PUE01 Insertado   "


    mensaje6 = mensaje + str(idPue01)


    try:
        busqueda = Cubes.objects.filter(CubeName="PUE02")
        idPue02 = busqueda[0].id
        mensaje = " Cube PUE02 YA EXISTE   "
    except:
        unCube = Cubes()
        unCube.CubeName="PUE02"
        unCube.idMaster = unMaster
        unCube.ip="4.4.4.4"
        unCube.usr="usrpue02"
        unCube.pwd="pwdpue02"
        unCube.save()
        idPue02 = unCube.id
        mensaje = " PUE02 Insertado   "


    mensaje7 = mensaje + str(idPue02)

    try:
        busqueda = Master.objects.filter(cityName="Culiacan")
        idCu = busqueda[0].id
        mensaje = " Culiacan ya existe= "
        unMaster = busqueda[0]
    except:
        unMaster = Master()
        unMaster.cityName = "Culiacan"
        unMaster.numTrunks = 100
        unMaster.save()
        idCu = unMaster.id
        mensaje = " Culiacan Insertado  "

    mensaje3 = mensaje + str(idCu)


    try:
        busqueda = Cubes.objects.filter(CubeName="CU01")
        idCu01 = busqueda[0].id
        mensaje = " Cube CU01 YA EXISTE   "
    except:
        unCube = Cubes()
        unCube.CubeName="CU01"
        unCube.idMaster = unMaster
        unCube.ip="5.5.5.5"
        unCube.usr="usrcu01"
        unCube.pwd="pwdcu01"
        unCube.save()
        idCu01 = unCube.id
        mensaje = " CU01 Insertado   "


    mensaje8 = mensaje + str(idCu01)


    try:
        busqueda = Cubes.objects.filter(CubeName="CU02")
        idCu02 = busqueda[0].id
        mensaje = " Cube CU02 YA EXISTE   "
    except:
        unCube = Cubes()
        unCube.CubeName="CU02"
        unCube.idMaster = unMaster
        unCube.ip="6.6.6.6"
        unCube.usr="usrcu02"
        unCube.pwd="pwdcu02"
        unCube.save()
        idCu02 = unCube.id
        mensaje = " CU02 Insertado   "

    mensaje9 = mensaje + str(idCu02)

    return HttpResponse(mensaje1 + mensaje4 + mensaje5 + mensaje2 +  mensaje6 + mensaje7 + mensaje3 + mensaje8 + mensaje9)

def logoutView(request):
    logout(request)
    return redirect('main')


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

        comando = "dial-peer voice " + str(DialPeer)+ " voip " + " \n" + "max-conn " + str(MaxCon) + " \n"
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



def validateDialPeerChange(ip, user, password,DialPeer,ActualMaxCon, NewMaxCon):
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

        comando = "show run dial-peer voice " + str(DialPeer) + " \n"
        connection.send("\n")
        connection.send(comando)
        time.sleep(0.5)

        # Checking command output for IOS syntax errors
        config = connection.recv(65535)

        # Closing the connection
        session.close()

        maxConDesc = "max-conn "

        lineas = config.split('\n');
        for line in lineas:

            index = line.rfind(maxConDesc)
            # if (line.startswith(maxConDesc)):
            if (index > 0):
                maxCon = line[len(maxConDesc):len(line)]
                maxCon = maxCon.replace(" ", "")
                maxCon = int(maxCon)

                if maxCon != ActualMaxCon:

                    return False
                else:
                    return True

        print("actual dial peer  " + config)

        return config

    except paramiko.AuthenticationException:
        print "* Invalid username or password. \n* Please check the username/password file or the device configuration!"
        print "* Closing program...\n"


@login_required
def viewCitiesFromMaster(request,masterName):

    usuario=request.user
    user = checkUserAuth(request.user)
    mensajeSalida=""

    if request.method== 'POST':

        updateCity=request.POST['updateCity']
        updateMaxConn=request.POST['updateMaxConn']
        newMaxConn = request.POST['newMaxConn']

        print("recibi peticion de actualizacion de la Cd: " + updateCity + "De Max= " + updateMaxConn + " A= " + newMaxConn)

        busqueda = City.objects.filter(CityName=updateCity)
        city = busqueda[0]
        DialPeer = city.DialPeer
        actualDBMaxCon = city.ActualMaxConn

        cube1_actualDBMaxCon = int(actualDBMaxCon) // 2
        cube2_actualDBMaxCon = int(actualDBMaxCon) // 2
        restante = int(actualDBMaxCon) % 2
        cube1_actualDBMaxCon = cube1_actualDBMaxCon + restante

        busqueda = Master.objects.filter(cityName=masterName)
        master = busqueda[0]
        idMaster = master.id

        print("DialPeer=  " + str(DialPeer))
        print("idmaster=  " + str(idMaster))

        busqueda = Master.objects.filter(cityName=masterName)
        master = busqueda[0]

        busqueda = Cubes.objects.filter(idMaster=idMaster)
        cube1 = busqueda[0]
        cube2 = busqueda[1]

        cube1_NewMaxCon = int(newMaxConn)//2
        cube2_NewMaxCon = int(newMaxConn) // 2
        restante = int(newMaxConn)%2
        cube1_NewMaxCon = cube1_NewMaxCon + restante

        cube1_ActualMaxCon= int(updateMaxConn)//2
        cube2_ActualMaxCon = int(updateMaxConn) // 2
        restante = int(updateMaxConn)%2
        cube1_ActualMaxCon = cube1_ActualMaxCon + restante


        if(cube1_actualDBMaxCon!=cube1_ActualMaxCon):
            print("Favor de syncronizar error")
            return render(request, "index.html",
                          {'citySelected': None, 'cities': None,
                           'mensajeSalida':"Error: Number of Max Connections does not match with actual config. Please reload or SYNC" })

        if (cube2_actualDBMaxCon != cube2_ActualMaxCon):
            print("Favor de syncronizar error")
            return render(request, "index.html",
                          {'citySelected': None, 'cities': None,
                           'mensajeSalida':"Error: Number of Max Connections does not match with actual config, Please reload or SYNC"})

        print("MaxCon Cube1=  " + str(cube1_NewMaxCon))
        print("MaxCon Cube2=  " + str(cube2_NewMaxCon))

        print("IP Cube1=  " + str(cube1.ip))
        print("IP Cube2=  " + str(cube2.ip))

        validate1=validateDialPeerChange(cube1.ip,cube1.usr, cube1.pwd,DialPeer, cube1_ActualMaxCon, cube1_NewMaxCon)

        if(validate1==False):
            print("Favor de syncronizar error")
            return render(request, "index.html",
                          {'citySelected': None, 'cities': None ,
                           'mensajeSalida':"Error: Number of Max Connections does not match with actual config. Please reload or SYNC"})

        validate2 = validateDialPeerChange(cube2.ip, cube2.usr, cube2.pwd, DialPeer, cube2_ActualMaxCon,
                                           cube2_NewMaxCon)
        if (validate2 == False):
            print("Favor de syncronizar error")
            return render(request, "index.html",
                          {'citySelected': None, 'cities': None,
                           'mensajeSalida':"Error: Number of Max Connections does not match with actual config. Please reload or SYNC"})

        ssh1= setDialPeerMaxCon(cube1.ip,cube1.usr, cube1.pwd,DialPeer, cube1_NewMaxCon)

        print("Se aplico cambio en Cube1= " + ssh1)

        ssh2 = setDialPeerMaxCon(cube2.ip, cube2.usr, cube2.pwd, DialPeer, cube2_NewMaxCon)

        city.ActualMaxConn=newMaxConn
        city.save()

        print("Se aplico cambio en Cube2= " + ssh2)
        mensajeSalida="Change Applied"

        mail_title = 'Cambio ' + updateCity + ' de ' + updateMaxConn + ' a ' + newMaxConn
        message = 'Usuario: ' + usuario.username + ' Realizo la siguiente modificacion: ' + mail_title
        email = settings.DEFAULT_FROM_EMAIL
        #recipients = "jgomez@sdnet.com.mx, jgodinez@sdnet.com.mx"
        recipients = "jgomez@sdnet.com.mx"
        print send_mail(mail_title, message, email, [recipients])
        print "Email Sent"

        #return render(request, "index.html", {'user': user, 'citySelected': masterName})




    busqueda = Master.objects.filter(cityName=masterName)
    master = busqueda[0]

    cities = City.objects.filter(idMaster=master)
    numTotalTrunks=0
    for city in cities:
        total = numTotalTrunks + city.ActualMaxConn
        numTotalTrunks  = total

    return render(request, "index.html",{'testvar':masterName,'citySelected':masterName, 'cities':cities, 'totalTrunk':numTotalTrunks,
                           'mensajeSalida':mensajeSalida})

@login_required
def viewSyncCities(request):

    mensaje = getCities("Guadalajara")

    mensaje = mensaje + "  " + getCities("Puebla")
    mensaje = mensaje + "  " + getCities("Culiacan")

    return render(request, "index.html",
                  {'citySelected': None, 'cities': None,
                           'mensajeSalida':"Sync Done   "})

@login_required
def viewAdmin(request,comando):
    usuario = request.user
    user = checkUserAuth(request.user)

    if(usuario.is_superuser!=True):
        mensajeSalida = "Error: Opcion solo para Super-User"
        messages.error(request,mensajeSalida)
        return redirect('main')
        return render(request, "index.html",
                      {'user': user, 'citySelected': None, 'mensajeSalida': mensajeSalida, 'admin': False})


    mensajeSalida ="Welcome Admin"

    if request.method== 'POST':

        name = request.POST['name']
        lastname = request.POST['lastname']
        email = request.POST['email']
        username=request.POST['username']
        password1=request.POST['password']
        password2 = request.POST['password2']

        if (name== ''):
            mensajeSalida = "Error: Favor de incluir Nombre"
            return render(request, "index.html",
                          {'user': user, 'citySelected': None, 'mensajeSalida': mensajeSalida, 'admin': True})
        if (lastname == ''):
            mensajeSalida = "Error: Favor de incluir Apellido"
            return render(request, "index.html",
                          {'user': user, 'citySelected': None, 'mensajeSalida': mensajeSalida, 'admin': True})

        if (email == ''):
            mensajeSalida = "Error: Favor de incluir email"
            return render(request, "index.html",
                          {'user': user, 'citySelected': None, 'mensajeSalida': mensajeSalida, 'admin': True})

        if(password1!=password2):
            mensajeSalida = "Error: Passwords no coinciden"
            return render(request, "index.html",
                          {'user': user, 'citySelected': None, 'mensajeSalida': mensajeSalida, 'admin': True})


        try:
            busqueda = User.objects.filter(username=username)
            usuarioEncontrado = busqueda[0]
            mensajeSalida = "Error: Usuario " + username + " ya existe"
        except:

            print ("Crear Usuario")
            try:
                newuser = User.objects.create_user(username, password=password1, first_name=name, last_name=lastname,email=email)
                newuser.save()
                #newuser.first_name = name
                #newuser.last_name = lastname
                #newuser.last_name = lastname
                #newuser.save()
                print("Usuario " + username + " creado")
                mensajeSalida = "Usuario " + username + " creado"
            except:
                mensajeSalida = "Error: al crear usuario"
        return render(request, "index.html",
                      {'user': user, 'citySelected': None, 'mensajeSalida': mensajeSalida, 'admin': True})

    if (comando=="listUsers/"):

        listUsers = User.objects.all()
        return render(request, "index.html",
                      {'user': user, 'citySelected': None, 'mensajeSalida': "LIST OF USERS", 'admin': True, 'listUsers':listUsers})

    return render(request, "index.html",
                  {'user': user, 'citySelected': None, 'mensajeSalida': mensajeSalida, 'admin': True})





