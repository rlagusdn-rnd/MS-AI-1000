echo admin123 | xhost + local:docker
docker start ms-ai
docker exec -it ms-ai sh -c "python3 /root/workspace/MS-AI_1000_v1.1_dev/main.py"
