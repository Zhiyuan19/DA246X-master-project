import topology


def ping(client, server, expected, count=1, wait=4):

    ping_result = client.cmd(f'ping {server.IP()} -c 1 -w 4')
    # print(ping_result)
    # ping_result = client.cmd(f'ping {server.IP()} -c 1 -w 4')
    # print(ping_result)

    cmd = f"ping {server.IP()} -c {count} -W {wait} >/dev/null 2>&1; echo $?"

    ret = client.cmd(cmd)

    print(client.name, client.IP())

    print(server.name, server.IP())

    # TODO: Here you should compare the return value "ret" with the expected value

    # (consider both failures

    print("client", client)

    print("server", server)

    print("ret value:", ret)

    if ret == 0:
        return expected

    else:
        return False


"""  previous implementation
def ping(client, server, expected, count=1, wait=3):
    print(server.IP())
    print(client.IP())
# tood: What if ping fails? How long does it take? Add a timeout to the command!

    pingTest = client.cmd('ping %s -c 2 -w 5'%server.IP())
    print(pingTest)

 
    cmd = f"ping {server.IP()} -c {count} -W {wait} >/dev/null 2>&1; echo $?"
    ret = client.cmd(cmd)

    print(ret)
    #tood: Here you should compare the return value "ret" with the expected value
    # (consider both failures)
    if ret.strip() == str(expected):
        print("ping has worked!")
        return True
    else:
        print("Not work")
        return False
    """


def curl(client, server, method="POST", payload="Group2", port=80, expected=True):
    """

    run curl for HTTP request. Request method and payload should be specified

    Server can either be a host or a string

    return True in case of success, False if not

    """

    #print(client.name, client.IP())
    #print(server.name, server.IP())


    if (isinstance(server, str) == 0):

        server_ip = str(server.IP())

    else:

        # If it's a string it should be the IP address of the node (e.g., the load balancer)

        server_ip = server

    # TODO: Specify HTTP method

    # TODO: Pass some payload (a.k.a. data). You may have to add some escaped quotes!

    # The magic string at the end reditect everything to the black hole and just print the return code
    #print(server_ip)
    #print(server)
    #print(client)

    cmd = f"curl --connect-timeout 3 --max-time 3 -X {method} -d '{payload}' -v -s {server_ip}:{port}/cgi-bin/index.cgi > /dev/null 2>&1; echo $? "

    ret = client.cmd(cmd).strip()

    print(f"`{cmd}` on {client} returned {ret}")

    # TODO: What value do you expect?


    if ret == "0":
        print("ret value:", ret)
        return True

    #else:
    #return False

    #return True  # True means "everyhing went as expected"