class CommandlineUserInterface:
    def __init__(self):
        pass

    # connect to the controlling server
    def connect(self):
        pass

    # disconnect to the controlling server
    def disconnect(self):
        pass

    # let the server ask all members in the network to report all new members
    # they know recently to the central server
    def refreshStatus(self):
        pass

    # retrieve clients information from the database
    def checkStatus(self):
        pass

    # request bots to execute certain piece of code
    # require:
    #     List of bot id
    #     the command to execute
    def executeCommand(self):
        pass

    # release the bot from the botnet
    # request the client to remove the botnet control software
    def releaseBot(self):
        pass
