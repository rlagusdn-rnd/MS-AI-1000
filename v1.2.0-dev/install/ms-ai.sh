echo admin123 | xhost + local:docker
docker start ms-ai
docker exec -it ms-ai sh -c "cd /root/workspace/MS-AI_1000/v1.2.0-dev && python3 main.py"
