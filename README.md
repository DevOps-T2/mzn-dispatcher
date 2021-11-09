# mzn-dispatcher

Dispatches solver runs as Kubernetes jobs

## Running during development

You have two options: Using [skaffold](https://skaffold.dev) or deploying
the service manually.

### Skaffold

```bash
skaffold dev --port-forward=services
```

### Manual

If using minikube:

```bash
eval $(minikube docker-env)
```

Then:

```bash
docker build -t mzn-dispatcher .
kubectl apply -f mzn-dispatcher.yaml
kubectl
```
