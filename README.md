# Image App

## 1. Introduction

Image App is a platform aiming to solve the image sharing problem. The platform acts as the middleman between a photo and sharing the photo elsewhere. The platform helps sharing photos by resizing images and making them optimised for sharing. The application is written in Python (FastAPI and Streamlit) and infrastructure is managed using Terraform and is hosted in Azure. This app is heavy in development thus not the final version.

The repository contains the pieces that are required for,

1. provisioning the infrastructure
2. configuring the infrastructure
3. application logic
4. frontend streamlit app
5. open telemetry collector

## 2.Getting Started

1. Provision the infrastructure following the guide [here](./infrastructure/README.md). By this point, the app must be available and accessible from the internet.
2. The docker compose configuration can be used for local development and hosting.
