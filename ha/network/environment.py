title = "Shadyglade network"
netStatDir = "/data/network/"
stateFileName = "network.json"
host = "elfo"
interface = "eth0"
ipAddr = "192.168.1.15"
router = "zog"
accessPoints = ["dundermifflin", "piedpiper", "initech", "wernhamhogg", "hooli"]
wiredHosts = ["gecko", "minnie", "pluto", "elfo", "oona",
              "holiday", "weather", "xmastree", "family-room-speakers",
              "piaware", "carcharger", "garage", "lights", "deck",
              "solar", "power", "pool", "backhouse", "hvac", "sprinklers",
              "Front door", "Driveway", "South", "North side", "Family room TV",
              "Family room Roku", "Back house Roku", "Darth", "solaredge", "raspberrypi",
             ]
hostAliases = {"00:17:EE:02:54:01": "Vonage",
               "28:EF:01:5D:6E:A6": "Bookworm",
               "F0:4F:7C:14:C9:12": "Winnies-kindle",
               "E4:7C:F9:67:22:C7": "Family room TV",
               "42:A3:6B:01:BC:F3": "onion",
               "00:27:02:10:49:20": "solaredge",
               "D4:6A:6A:54:23:82": "ollie",
               "68:FF:7B:80:DD:1D": "garageLights",
               "D8:0D:17:19:6D:45": "deckLights",
               "D8:0D:17:19:8B:0C": "trashLights",
               "68:FF:7B:BA:4E:7E": "backHouseMusic",
               "68:FF:7B:BA:52:B9": "familyRoomLamp",
               "B0:BE:76:FE:16:30": "backLights",
              }
ignoreHosts = {"router", "house",
               "prod.solaredge.com", "prod2.solaredge.com", "prod3.solaredge.com",
              }
networks = {
            "spectrum": {
                "interface": "eth0",
                "router": "192.168.1.1",
                "gateway": "76.169.48.1",
                "internet": "metrics.buehl.co",
                },
            }
maxPingTime = 5
