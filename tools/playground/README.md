# ARouteServer playground

[![Playground tests status](https://github.com/pierky/arouteserver/workflows/Playground%20tests/badge.svg)](https://github.com/pierky/arouteserver/actions?query=workflow%3A%22Playground+tests%22)

This is a Docker-based playground that can be use to experiment with ARouteServer.

It offers and environment with several actors, configured to represents specific scenarios that can often be found on a real IX platform: a route server, some clients that announce some good and some bad routes, a looking glass.

The idea is to let the users play with the whole environment and see how easy it is to deploy a secure, feature-rich route server.

## How to play

Docker is needed on the local machine (setup instructions can be found [here](https://docs.docker.com/get-docker/)).

Once it's installed, it's just a matter of cloning this repository and using `docker-compose` to spin up the environment:

```
$ git clone https://github.com/pierky/arouteserver.git
[... omitted...]
$ cd arouteserver/tools/playground
$ docker-compose build
[... omitted...]
$ docker-compose up -d
Creating network "playground_peering_fabric" with the default driver
Creating arouteserver_playground_rs       ... done
Creating arouteserver_playground_client_1 ... done
Creating arouteserver_playground_alicelg  ... done
Creating arouteserver_playground_client_2 ... done
```

This will spin up the a BIRD-based route server and some clients, and once the route server will be configured and ready to work, also an instance of [Alice-LG](https://github.com/alice-lg/alice-lg) will be executed and connected to the route server.

Some fictitious BGP announcements are simulated in order to reproduce situations that can be normally found in real IX route servers.

Unfortunately most of the AS numbers and IP prefixes used in this example have to be *real*, not from the example/documentation ranges, otherwise the route server would reject all of them because of their own nature.

Users willing to simulate more "weird" situations are strongly encouraged to use the existing clients as a template and to add more BGP announcements.

Expectations can be checked by "logging in" into the route server or client instances and querying the local BGP daemon:

```
$ docker-compose exec client_2 bash
root@ee27954906b9:~# birdc show route
BIRD 1.6.3 ready.
192.136.136.0/24   unreachable [own_prefixes 16:24:32] * (200)
193.0.0.0/21       via 10.0.0.11 on eth0 [the_rs 16:24:57 from 10.0.0.2] * (100) [AS3333i]
```

Also, the Alice-LG WEB interface can be used to check the routes received by the route server, and their status: http://127.0.0.1:8080/routeservers/rs1-example-com/protocols/AS3333_1/routes?ne=0&q=202.12.29.0

**Please note:** the route server that is spun up will be automatically configured by the provisioning script *rs/run.sh*.
If the user desires to manually setup and configure ARouteServer and build a BIRD configuration from scratch (which is strongly recommended for the actual end goal of this playground), the *docker-compose.yml* file can be edited and the environment variable `SETUP_AND_CONFIGURE_AROUTESERVER` set to 0. The playground can then be recreated using `docker-compose down` / `docker-compose up -d`: at this point, the *rs* instance will only have a running *vanilla* BIRD instance and all the required dependencies setup. The users will be able to connect to it (`docker-compose exec rs bash`) and work on it. [SETUP_GUIDELINES.md](SETUP_GUIDELINES.md) contains some hints on how to configure it.

## Actors

The following containers are used in this playground.

### Route server

- Docker instance name: rs

- ASN: 64500

- IP: 10.0.0.2

This is where ARouteServer is also installed.

It's not ideal for production environments to run the tool on the same machine where the BGP daemon also runs, specially when there are lots of clients (and thus the configuration building process requires a significant amount of memory), but this is just a playground!

### Client 1

- Docker instance name: client_1

- ASN: 3333

- IP: 10.0.0.11

#### Announcements from this client

This client announces the following routes to the route server:

- **193.0.0.0/21**: this should be accepted, unless the IRR records or ROAs for the real life network that actually owns this prefix (RIPE NCC) will change in the future.

- **193.0.0.1/32**: this should be dropped, RPKI INVALID.

- **10.0.0.0/24**: this is the playground IX peering LAN prefix, so assuming that 10.0.0.0/24 was correctly configured during the ARouteServer setup (`configure` command) the route will be rejected with the reason "Prefix is in global blacklist" (otherwise, it will be rejected because it's a bogon).

- **192.168.0.0/24**: this will be dropped too: it's a bogon.

- **193.0.22.0/23**: this will be accepted, but for the sake of the example, let's assume that the origin network doesn't want it to be announced to AS10745, thus we'll add the BGP community "do not announce to AS10745" in the outbound filter of the client BGP speaker.

- **202.12.29.0/24**, **AS_PATH 3333 4608**: this is a prefix that in the real life is originated by AS4608; for the sake of the example, let's assume that in this playground AS3333 is propagating a route that they learn from AS4608 to the route server. Neither the prefix nor AS4608 are part of the IRR object [AS-RIPENCC](https://apps.db.ripe.net/db-web-ui/lookup?source=ripe&key=AS-RIPENCC&type=as-set), which ARouteServer automatically fetches from [AS3333's PeeringDB record](https://www.peeringdb.com/asn/3333), thus the route is rejected.

### Client 2

- Docker instance name: client_2

- ASN: 10745

- IP: 10.0.0.12

#### Announcements from this client

This client announces the following routes to the route server:

- 192.136.136.0/24, this should be accepted, unless the IRR records or ROAs for the real-life network that actually owns this prefix (ARIN) will change in the future.

### Alice-LG

- Docker instance name: alice_lg

- IP: 10.0.0.3

- WEB interface: http://127.0.0.1:8080
