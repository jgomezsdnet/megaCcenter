from models import Master

unMaster = Master()
unMaster.cityName = "Guadalajara"
unMaster.numTrunks = 300
unMaster.save()

dosMaster = Master()
dosMaster.cityName = "Puebla"
dosMaster.numTrunks = 300
dosMaster.save()

tresMaster = Master()
tresMaster.cityName = "Culiacan"
tresMaster.numTrunks = 100
tresMaster.save()


