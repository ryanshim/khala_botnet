# Need to determine if this is running on the client or cnc server.
# The cli class has methods that seem to mix w/ those that should be separated.
# For now, I will assume that this script is running on the cnc server.
import argparse

class CommandlineUserInterface:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        # Add cli options
        self.parser.add_argument("-c", "--conn", type=str, help="Connect to" + \
                " a client.", metavar='')

        self.parser.add_argument("-d", "--disconn", help="Disconnect from " + \
                "the client.", metavar='')

        self.parser.add_argument("-r", "--refresh", help="Refresh and ask " + \
                "all members in network to report any new members to the " + \
                "central server.", metavar='')

        self.parser.add_argument("-ch", "--check", help="Check in on client " + \
                "by retrieving client information from the database.", metavar='')

        self.parser.add_argument("-x", "--exec", type=str,
                help="Request bots to execute DDoS on specified victim.",
                metavar='')

        self.parser.add_argument("-rel", "--release", type=str,
                help="Release specified bot from the botnet and remove" + \
                        "botnet software on client.", metavar='')

        self.args = self.parser.parse_args()
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

cli = CommandlineUserInterface()
print(cli.args)
