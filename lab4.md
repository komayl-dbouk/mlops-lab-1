Question 1: 

Without a mounted volume, everything under /mlflow-data lives only in that container's own writable layer. docker stop keeps it (container still exists, just stopped), but docker rm deletes the writable layer permanently. Starting a new container from the same image gives you a fresh, empty /mlflow-data



Question 2:

 A named volume is managed by Docker (lives under Docker's own storage area, independent of any host path)it survives docker compose down without extra flags, and doesn't require a pre-existing folder or care about host file permissions. A bind mount would technically work the same for persistence


Question 3:

 Because both containers will be on the same Docker Compose–created network, and Compose runs an embedded DNS server on that network that automatically registers each service's name (mlflow) as a resolvable hostname pointing to that container's IP. host.docker.internal/--network host were needed in Lab 3 because the target (your host's MLflow) was outside Docker entirely — no container-to-container DNS applies to the host machine.


 Question 4:

 Hardcoding http://inference:8000 bakes in an assumption that only holds inside this specific Compose network — the hostname inference only resolves there. If you ever ran the frontend image standalone, a different Compose project's service name, or even just pointed it at a remote/staged inference API for testing, a hardcoded URL would be flat-out wrong and require rebuilding the image just to change where it talks to. 


 Question 5:

 inference doesn't publish a port because nothing outside Docker ever needs to reach it directly — only frontend talks to it, and frontend is a container on the same Compose network. Compose's internal DNS resolves http://inference:8000 to the container's private IP on that network, and every container's ports are reachable from other containers on the same network by default, regardless of whether they're published to the host. 


 Question 6:

 Our serve.py calls mlflow.pyfunc.load_model(...) inside the FastAPI lifespan startup hook with no retry logic — if mlflow:5000 refuses the connection because the server isn't listening yet, that call raises, the lifespan context manager propagates the exception, and uvicorn logs ERROR: Application startup failed. Exiting. and exits with a non-zero code. Since there's no restart: policy set in the compose file, the inference container just stays stopped/exited


 Question 7:

mlflow and frontend would show a PORTS entry (0.0.0.0:5000->5000/tcp and 0.0.0.0:8501->8501/tcp), and inference would show blank in that column — because only mlflow and frontend have a ports: mapping in the compose file; inference has none.
Yes, it does match the expectation


Question 8:

The old one — serve.py loads the model exactly once, in the lifespan startup hook, and holds it in memory for the life of the process. Promoting a new version in the registry only changes a pointer in MLflow's backend store

The single command: docker compose restart inference. This stops and restarts just that container (no rebuild — same image, same code, same .venv),  and this time it resolves to whatever version the alias currently points to.



Question 9:

nothing about which model version to serve is stored in the image at all — the image only contains the Python interpreter, dependencies, and serve.py's code, which says "ask the registry which version @champion/@staging currently points to" rather than "here are the literal weights."

the image is a fixed, versioned artifact (code + deps), completely decoupled from model versioning. The model is 100% a runtime dependency, re-fetched fresh on every process start, never persisted in the image. That separation is the whole point: it lets you ship one image and roll model versions forward and backward purely through registry changes + a restart, with deploys and model promotions on entirely independent cadences


Question 10:

Without -v (docker compose down + up): yes — food11 v2 and its champion alias are still there, and inference starts up fine. docker compose down only stops and removes containers; the named volume mlflow-data
With -v (docker compose down -v + up): everything's gone — querying food11 returns RESOURCE_DOES_NOT_EXIST, and inference fails to start with the same "model not found" error as a totally fresh setup. The -v flag explicitly deletes the named volumes along with the containers, so the new mlflow container starts with a brand-new empty volume


Question 11:


3 replicas + load balancer: Compose can scale containers (--scale) but has no built-in load balancer, cross-node scheduling, or health-aware routing — needs a real orchestrator (Kubernetes/Swarm) or an external LB (nginx/Traefik).
mlflow surviving machine failure: Compose only restarts on the same host, and the named volume lives on that host's disk — both die with the machine. Needs multi-node orchestration to reschedule the server, plus swapping SQLite for a managed/replicated DB and the local volume for object storage (S3/GCS) so state isn't tied to one host at all.
