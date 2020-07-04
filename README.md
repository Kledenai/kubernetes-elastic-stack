# Elastic Stack K8s

Edureka course project

The purpose of this project is to provide starter files for deploying a high performance Elasticsearch cluster on Kubernetes running on either Google Computer Engine.  

The configuration files will generally be targeted at deployments with at least two nodes, four or more CPUs, and fifteen or more GBs of memory.  However, for the purposes of testing the components with less hardware available, there is also a profile that will run on a single node Kubernetes cluster which you can easily set up with minikube. If you really wanted to run Elasticsearch on a single computer, you would just use one container to do it.  Our Elasticsearch cluster will have three master nodes, and multiple data and ingest nodes, which you can adjust the number of to meet your hardware requirements.

## minikube

To test the configuration on MaxOS X, `minikube` can be installed to launch a local one node Kubernetes cluster.  When starting minikube, increase the default machine size:

`minikube start --memory 8192 --disk-size 50g --cpus 4`
