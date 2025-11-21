Requirements:

1) tshark
2) docker

The script takes two inputs:

1) user/repository_name (iambcl/pcap_docker for instance)
2) docker compose file location (relative to repository folder)

It will take a pcap while running the container. 

- If it creates its own network, then it will take a pcap on the docker bridge for that network.
  
- If it uses the default docker network, then the pcap will be taken on the default docker bridge.
  - If there is any other container running on the default docker bridge, you can edit the tshark command to ignore the IP so that when subprocess runs the command, it will not be captured.
