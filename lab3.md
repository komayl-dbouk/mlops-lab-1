Question1:

the version number was my model given is 1.

-Logged model artifact tied permanently to one specific run, it's just files on disk 

-Registered model is a named, versioned entity in the Model Registry, decoupled from any single run's artifact path. Each time you register a new logged artifact under that name, it gets a new version number 



Question2:

the aliases replacing the old built is champion

Version separately from the run: runs are messy experiment history (failed attempts, sweeps); registry versions are a clean, stable lineage of only the artifacts worth deploying.
Alias vs fixed stage: stages are a rigid, global fixed set (Staging/Production); aliases are mutable pointers you name yourself, unlimited in number 



Question3:

a raw .pth is just tensor weights — it has no record of the model architecture, preprocessing, class mapping, or environment needed to run it; whoever loads it has to know and reconstruct all of that out-of-band. 

loading a self describing package resolves through the registry rather than a hardcoded path — so the serving code never needs to know a run ID or filesystem location at all, and the same URI keeps working as the underlying artifact changes.

To serve a newer version: you just move the champion alias in the registry to point at the new version



Question4:

 Docker caches each layer and only invalidates a layer, and when its inputs change. uv sync is by far the slowest step here.By copying only the dependency manifests first and running uv sync before copying src/, that expensive layer's cache key depends only on pyproject.toml/uv.lock — not on my application code.

 if i change a line in serve.py: pyproject.toml/uv.lock are unchanged, so Docker reuses the cached builder stage entirely, So the rebuild is near-instant instead of taking minutes. 



Question5:

Naive single-stage: would be bigger, roughly 1.5–2x — because it keeps uv's own wheel/download cache and the uv binary itself baked into the final image

Multi-stage avoids this because only the finished .venv gets copied into the runtime stage


question6:

Speed: entire context (incl. data/'s 36k images, .venv/, .git/) gets tarred and sent to the daemon on every build — slow, and can invalidate cache unnecessarily.

.venv/ — it's a Windows-built venv with platform-specific compiled binaries, incompatible with the Linux container; the rest (data/, mlruns/, mlflow.db, .git/) just waste time/space, they don't break anything.



question7:

127.0.0.1/localhost is loopback — it always refers to the container's own network namespace, not the host's. By default Docker gives each container its own isolated network namespace (a virtual eth0 on a bridge network), so 127.0.0.1 inside the container is a different "machine" than 127.0.0.1 on your host — the MLflow server bound to the host's loopback interface is simply unreachable from there. 

host.docker.internal resolves to: a special DNS name Docker Desktop injects into the container's network, resolving to the IP address of the host machine as seen from inside Docker's internal virtual network


question8:

I ran two independent containers from the same mlops-lab-1:test image with nothing rebuilt in between. Both went through the identical sequence — startup hook calls 

Baked into the image, identical on every container regardless of network

Fetched at runtime, re-resolved fresh on every single start: which model version @champion points to, and the weights themselves