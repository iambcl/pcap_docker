import os, subprocess, re, time, json

if __name__ == '__main__':
    repo_path = input("Repo path: ")
    repo_cwd = repo_path.split("/")[-1]
    if os.path.isdir(f"test_old/{repo_cwd}"):
        subprocess.run(["mv",f"test_old/{repo_cwd}", "."])
    elif os.path.isdir(repo_cwd) == False:
        clone_cmd = ["git", "clone", f"https://www.github.com/{repo_path}"]
        subprocess.run(clone_cmd, check=True)
    docker_compose_filepath = input("docker compose files: ").split(",")
    docker_compose_commands = ['docker','compose']
    for compose_path in docker_compose_filepath:
        docker_compose_commands.append("-f")
        docker_compose_commands.append(compose_path)

    while True:
        g = input("Press g when ready to proceed: ")
        if g == 'g':
            break

    build_command = docker_compose_commands + ["up", "--no-start"] #Build the containers
    build_result = subprocess.run(
        build_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=repo_cwd,
        timeout=300
    )

    networks = subprocess.check_output(["sudo", "docker", "network", "ls", "--filter", f"label=com.docker.compose.project={repo_cwd.lower()}"]).decode()

    pattern = r"(\S+)\s+(\S+)\s+(?:bridge|host|overlay|macvlan|none|custom)\s+local"
    bridges = []
    subnets = []
    # find all the network ID and names in the output using the regular expression pattern
    matches = re.findall(pattern, networks)

    if matches:
        # print all the network ID and names to the console
        for network_id, network_name in matches:
            bridges.append("br-" + network_id)
            out = subprocess.check_output(["sudo", "docker", "network", "inspect", network_id])
            info = json.loads(out)[0]
            cfgs = (info.get("IPAM") or {}).get("Config") or []
            for cfg in cfgs:
                # cfg may contain Subnet, Gateway, and/or IPv6 fields
                subnet = cfg.get("Subnet")
                if subnet:
                    subnets.append((network_name,subnet))
    else:
        print("Network ID and names not found in the output.")

    if bridges == []:
        bridges = ["docker0"]
    

    up_command = docker_compose_commands + ["up", "-d"]
    up_result = subprocess.run(
        up_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=repo_cwd,
        start_new_session=True
    )

    outputfile = f'test_pcap/{repo_cwd}.pcap'
    tsharkcmd = ["sudo","tshark"]
    for bridge in bridges:
        tsharkcmd.append("-i")
        tsharkcmd.append(bridge)
    tsharkcmd.append("-w")
    tsharkcmd.append(outputfile)

    #Force it to save in .pcap format instead of pcapng
    tsharkcmd.append("-F")
    tsharkcmd.append("pcap")

    print("Listening on bridges: ", bridges)
    print(tsharkcmd)

    subprocess.Popen(["touch", outputfile])
    subprocess.Popen(["chmod", "o=rw", outputfile])
    subprocess.Popen(tsharkcmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


    time.sleep(5)

    while True:
        s = input("Type stop when ready to stop.")
        if s == 'stop':
            break
        
    subprocess.run(
    docker_compose_commands + ["down", "--remove-orphans", "--volumes", "--rmi", "all"],
    cwd=repo_cwd,
    )

    move_command = ["mv",repo_cwd,"test_old"]
    subprocess.run(
        move_command
    )