#!/bin/bash
docker build --tag toadbot .
docker stop toadbot
docker rm toadbot
docker run -d --name toadbot --restart unless-stopped toadbot