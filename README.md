# Project Documentation: ASR Service, Elastic Backend, and Frontend (Search UI)

This README provides comprehensive instructions for setting up, running, and deploying the Automatic Speech Recognition (ASR) service, Elastic Backend, and React Frontend (Search UI) components of this project.

## Table of Contents

1.  [Automatic Speech Recognition Service and Tooling](#1-automatic-speech-recognition-service-and-tooling)
    * [Overview](#overview)
    * [Running the ASR Service Locally](#running-the-asr-service-locally)
    * [Docker Containerization](#docker-containerization)
2.  [Elastic Backend](#2-elastic-backend)
    * [Overview](#overview-1)
    * [Running the Elastic Backend Locally](#running-the-elastic-backend-locally)
    * [Docker Compose](#docker-compose)
    * [Populating Elasticsearch with Data](#populating-elasticsearch-with-data)
3.  [Frontend (Search UI)](#3-frontend-search-ui)
    * [Overview](#overview-2)
    * [Running the Frontend Locally](#running-the-frontend-locally)
    * [Production Build Configuration](#production-build-configuration)
4.  [Deployment to Azure Cloud VM](#4-deployment-to-azure-cloud-vm)
    * [Step 1: Create and Configure Your Azure Virtual Machine (VM)](#step-1-create-and-configure-your-azure-virtual-machine-vm)
    * [Step 2: Connect to Your VM and Install Docker](#step-2-connect-to-your-vm-and-install-docker)
    * [Step 3: Deploy Your Backend (Elasticsearch & Kibana)](#step-3-deploy-your-backend-elasticsearch--kibana)
    * [Step 4: Deploy Your Frontend (React App)](#step-4-deploy-your-frontend-react-app)
    * [Step 5: Populate Elasticsearch with Data on VM](#step-5-populate-elasticsearch-with-data-on-vm)
    * [Step 6: (Optional) Configure Custom Domain and SSL (HTTPS)](#step-6-optional-configure-custom-domain-and-ssl-https)
5.  [Important Considerations](#5-important-considerations)

---

## 1. Automatic Speech Recognition Service and Tooling

### Overview
The ASR service is implemented in the `asr` directory and provides speech-to-text functionality via a FastAPI application.

### Running the ASR Service Locally
1.  Ensure you have Python installed (preferably Python 3.8+).
2.  Activate your Python virtual environment:
    ```bash
    source /Users/chewhongjun/gits/HTXAssessment/htx-venv/bin/activate
    ```
3.  Navigate to the `asr` directory:
    ```bash
    cd asr
    ```
4.  Install dependencies if not already installed:
    ```bash
    pip install -r ../requirements.txt
    ```
5.  Run the ASR API server:
    ```bash
    uvicorn asr_api:app --host 0.0.0.0 --port 8001
    ```

### Docker Containerization
* A `Dockerfile` is provided in the `asr` directory to containerize the ASR service.
* To build the Docker image:
    ```bash
    docker build -t asr-api ./asr
    ```
* To run the container:
    ```bash
    docker run -p 8001:8001 asr-api
    ```

---

## 2. Elastic Backend

### Overview
The Elastic backend is located in the `elastic-backend` directory and handles indexing and search functionalities using Elasticsearch and Kibana.

### Running the Elastic Backend Locally
1.  Activate your Python virtual environment:
    ```bash
    source /Users/chewhongjun/gits/HTXAssessment/htx-venv/bin/activate
    ```
2.  Navigate to the `elastic-backend` directory:
    ```bash
    cd elastic-backend
    ```
3.  Install dependencies if needed:
    ```bash
    pip install -r ../requirements.txt
    ```
4.  Run the backend scripts, for example, to index data (ensure Elasticsearch is running first, see Docker Compose section below):
    ```bash
    python cv-index.py
    ```
5.  The Elastic backend primarily runs as Docker containers. There isn't a separate "backend server" script in this directory beyond the indexing script.

### Docker Compose
* There is a `docker-compose.yml` in the `elastic-backend` directory for orchestrating Elasticsearch and Kibana services.
* To start the services (Elasticsearch and Kibana):
    ```bash
    docker-compose up -d
    ```
    (Note: Use `docker-compose` with a hyphen, not `docker compose`).
* To stop the services:
    ```bash
    docker-compose down
    ```
* You can verify the services are running:
    * `docker ps`
    * Elasticsearch health: `curl http://localhost:9200/_cat/health?v`
    * Kibana UI: `http://localhost:5601`

### Populating Elasticsearch with Data
The `cv-index.py` script is used to load data from a CSV file into your Elasticsearch index.

1.  **Ensure Elasticsearch is running** (using `docker-compose up -d` as described above).
2.  **Adjust `cv-index.py` path:** Open `elastic-backend/cv-index.py` and ensure `TRANSCRIPTION_CSV_PATH` correctly points to your `cv-valid-dev_transcribed.csv` file. For example, if the CSV is in `../cv-valid-dev/`, the path should be correct.
3.  **Run the indexing script:**
    ```bash
    cd elastic-backend
    python cv-index.py
    ```

---

## 3. Frontend (Search UI)

### Overview
The frontend is located in the `search-ui` directory and is a React-based application built with Vite.

### Running the Frontend Locally
1.  Navigate to the `search-ui` directory:
    ```bash
    cd search-ui
    ```
2.  Install dependencies:
    ```bash
    yarn install
    ```
    (or `npm install` if you prefer npm)
3.  Run the development server:
    ```bash
    yarn dev
    ```
    (or `npm run dev`)
4.  Access the frontend in your browser at `http://localhost:5173/elasticsearch-htx`.
    * **Important:** Your local React development server (`http://localhost:5173`) will attempt to connect to Elasticsearch on your Azure VM. Ensure your `docker-compose.yml` on the VM has `http.cors.allow-origin=http://localhost:5173,...` configured for Elasticsearch.

### Production Build Configuration
The React application is configured to be served from a subpath (`/elasticsearch-htx/`) in a production environment.

1.  **`vite.config.js` Configuration:**
    Ensure your `vite.config.js` file (located in your `search-ui` directory) is configured as follows to handle the base path:

    ```javascript
    import { defineConfig } from "vite";
    import react from "@vitejs/plugin-react"; // Import the React plugin

    // [https://vitejs.dev/config/](https://vitejs.dev/config/)
    export default defineConfig({
      // Set the base public path for your application
      // If your app is served from [http://yourdomain.com/elasticsearch-htx/](http://yourdomain.com/elasticsearch-htx/),
      // then the base should be '/elasticsearch-htx/'.
      base: "/elasticsearch-htx/",
      plugins: [react()], // Use the React plugin
      resolve: {
        alias: {
          // Assuming your source code is in the 'src' directory
          "@": "/src",
        },
      },
      build: {
        // Ensure the output directory is 'dist' (default for Vite)
        outDir: "dist",
      },
    });
    ```

2.  **Build the production assets:**
    ```bash
    yarn build
    ```
    (or `npm run build`)
    This will create an optimized `dist` directory.

3.  **Serve the built files:**
    You will serve the `dist` directory using a static file server (like Nginx) or configure your backend to serve it. Ensure the server is configured to serve the frontend under the `/elasticsearch-htx` base path.

---

## 4. Deployment to Azure Cloud VM

This section details the steps to deploy your entire application stack to an Azure Virtual Machine.
**Your Azure VM Public IP:** `20.6.88.232`
**Your Azure VM Username:** `chewhongjun`

### Step 1: Create and Configure Your Azure Virtual Machine (VM)

1.  **Log in to Azure Portal:** Go to [portal.azure.com](https://portal.azure.com/).
2.  **Create a Resource Group:** (Optional, but recommended for organization)
    * Click `Resource groups` -> `Create`.
    * Give it a name (e.g., `ElasticSearchAppRG`) and choose a region.
3.  **Create a Virtual Machine:**
    * Click `Virtual machines` -> `Create` -> `Azure virtual machine`.
    * **Basics:**
        * **Subscription:** Your Azure subscription.
        * **Resource Group:** Select the one you created or create a new one.
        * **Virtual machine name:** `elastic-search-vm`
        * **Region:** Select a region close to your users.
        * **Image:** Choose an Ubuntu Server LTS image (e.g., `Ubuntu Server 22.04 LTS - Gen2`).
        * **Size:** Start with a `Standard_B2s` (2 vcpus, 4 GiB memory) or `Standard_B4ms` (4 vcpus, 16 GiB memory) for Elasticsearch. Monitor performance and scale up if needed.
        * **Authentication type:** `Password` (as per your setup).
        * **Username:** `chewhongjun`
    * **Disks:** Consider adding a separate data disk (Standard SSD or Premium SSD) for Elasticsearch data persistence.
    * **Networking:**
        * **Public IP:** (New) This is how you'll access your VM.
        * **NIC network security group:** Select `Advanced`.
        * **Configure network security group:**
            * **Add inbound port rules** to allow traffic:
                * `22` (SSH - Source IP `My IP` for security, or `Any` for testing).
                * `80` (HTTP - For Nginx, Source `Any`).
                * `443` (HTTPS - For Nginx with SSL, Source `Any`).
                * `5173` (React dev server if serving directly, Source `Any`).
                * `9200` (Elasticsearch HTTP, Source `Any`).
                * `5601` (Kibana, Source `Any`).
    * **Review + create:** Review your settings and click `Create`.

### Step 2: Connect to Your VM and Install Docker

1.  **Get VM Public IP:** Note your VM's `Public IP address` from the Azure Portal (`20.6.88.232`).
2.  **SSH into your VM:**
    ```bash
    ssh chewhongjun@20.6.88.232
    ```
    You will be prompted to enter your password.
3.  **Update Package List:**
    ```bash
    sudo apt update
    ```
4.  **Install Docker Engine:**
    ```bash
    sudo apt install docker.io -y
    ```
5.  **Start and Enable Docker:**
    ```bash
    sudo systemctl start docker
    sudo systemctl enable docker
    ```
6.  **Add your user to the `docker` group:**
    ```bash
    sudo usermod -aG docker $USER
    newgrp docker # Apply group changes immediately (or log out/in)
    ```
7.  **Verify Docker Installation:**
    ```bash
    docker run hello-world
    ```
8.  **Install Docker Compose:**
    ```bash
    sudo apt install docker-compose -y
    # Verify: docker-compose version
    ```

### Step 3: Deploy Your Backend (Elasticsearch & Kibana)

1.  **Copy `docker-compose.yml` to VM:**
    From your local machine, navigate to your `elastic-backend` directory and use `scp`:
    ```bash
    scp ./docker-compose.yml chewhongjun@20.6.88.232:/home/chewhongjun/docker-compose.yml
    ```
    You will be prompted for your password.

2.  **Modify `docker-compose.yml` for VM Environment and CORS:**
    SSH into your VM and open `/home/chewhongjun/docker-compose.yml` with a text editor (e.g., `nano`):
    ```bash
    nano /home/chewhongjun/docker-compose.yml
    ```
    Ensure the `environment` section for your `es01` service (and any other Elasticsearch nodes) includes the following CORS settings. This is crucial for your React frontend to communicate with Elasticsearch.

    ```yaml
    services:
      es01:
        image: elasticsearch:8.10.2
        container_name: es01
        environment:
          - discovery.type=single-node
          - xpack.security.enabled=false
          - http.cors.enabled=true
          - http.cors.allow-origin=http://localhost:5173,[http://20.6.88.232:80](http://20.6.88.232:80),[http://20.6.88.232:5173](http://20.6.88.232:5173),[http://20.6.88.232/elasticsearch-htx](http://20.6.88.232/elasticsearch-htx) # IMPORTANT: Add all origins your frontend might use
          - http.cors.allow-headers=X-Requested-With,Content-Type,Content-Length,Authorization,Access-Control-Allow-Headers,Accept
          - http.cors.allow-methods=POST,OPTIONS,GET
        volumes:
          - esdata01:/usr/share/elasticsearch/data
        ports:
          - 9200:9200
          - 9300:9300
        networks:
          - elastic
    
      es02: # If you have a second node, ensure it also has CORS settings if needed
        image: elasticsearch:8.10.2
        container_name: es02
        environment:
          - discovery.type=single-node
          - xpack.security.enabled=false
          - http.cors.enabled=true
          - http.cors.allow-origin=http://localhost:5173,[http://20.6.88.232:80](http://20.6.88.232:80),[http://20.6.88.232:5173](http://20.6.88.232:5173),[http://20.6.88.232/elasticsearch-htx](http://20.6.88.232/elasticsearch-htx)
          - http.cors.allow-headers=X-Requested-With,Content-Type,Content-Length,Authorization,Access-Control-Allow-Headers,Accept
          - http.cors.allow-methods=POST,OPTIONS,GET
        volumes:
          - esdata02:/usr/share/elasticsearch/data
        ports:
          - 9201:9200 # Example for a second node
          - 9301:9300
        networks:
          - elastic
    
      kibana:
        image: kibana:8.10.2
        container_name: kibana-app
        ports:
          - 5601:5601
        environment:
          - ELASTICSEARCH_HOSTS=http://es01:9200,http://es02:9200 # Point to both ES nodes
        networks:
          - elastic
        depends_on:
          - es01
          - es02
    
    volumes:
      esdata01:
        driver: local
      esdata02:
        driver: local
    
    networks:
      elastic:
        driver: bridge
    ```
    Save and exit.

3.  **Run Docker Compose Services:**
    In the directory where `docker-compose.yml` is located on your VM:
    ```bash
    docker-compose up -d
    ```
    Wait a few minutes for the services to start and stabilize.

4.  **Verify Backend Services:**
    * Check running containers: `docker ps`
    * Check Elasticsearch health: `curl http://localhost:9200/_cat/health?v` (should eventually be `green` or `yellow`).
    * Access Kibana in your browser: `http://20.6.88.232:5601`

### Step 4: Deploy Your Frontend (React App)

Choose one of the following options:

#### Option A: Using Nginx (Recommended for Production)

Nginx is a robust web server that can serve your static React files and act as a reverse proxy for your Elasticsearch and Kibana services.

1.  **Build your React App Locally (using Vite and Yarn):**
    On your local machine, navigate to your `search-ui` directory and run:
    ```bash
    yarn install
    yarn build
    ```
    This will create a `dist` folder containing your optimized static files, configured for the `/elasticsearch-htx/` base path.

2.  **Copy React Build to VM:**
    Use `scp` to copy the `dist` folder to your VM:
    ```bash
    scp -r ./search-ui/dist chewhongjun@20.6.88.232:/var/www/html/elasticsearch-htx
    ```
    (The destination path `/var/www/html/elasticsearch-htx` assumes you want to serve it under that subpath).

3.  **Install Nginx on VM:**
    SSH into your VM:
    ```bash
    sudo apt install nginx -y
    ```

4.  **Configure Nginx:**
    Create a new Nginx configuration file (`sudo nano /etc/nginx/sites-available/react-app`):
    ```nginx
    server {
        listen 80;
        listen [::]:80;
        server_name 20.6.88.232; # Or your custom domain if configured

        root /var/www/html/elasticsearch-htx; # Path to your React build folder
        index index.html index.htm;

        location /elasticsearch-htx/ {
            try_files $uri $uri/ /elasticsearch-htx/index.html;
        }

        # Reverse proxy for Elasticsearch
        location /es/ {
            proxy_pass http://es01:9200/; # 'es01' is the Docker service name
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            # CORS headers for Nginx to allow frontend to talk to ES through proxy
            add_header 'Access-Control-Allow-Origin' '*' always; # Adjust to specific origin in production
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
            add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain charset=UTF-8';
                add_header 'Content-Length' 0;
                return 204;
            }
        }

        # Reverse proxy for Kibana (optional)
        location /kibana/ {
            proxy_pass http://kibana:5601/; # 'kibana' is the Docker service name
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_cache_bypass $http_upgrade;
        }
    }
    ```
    Save and exit.

5.  **Enable Nginx Configuration:**
    ```bash
    sudo ln -s /etc/nginx/sites-available/react-app /etc/nginx/sites-enabled/
    sudo unlink /etc/nginx/sites-enabled/default # Disable default Nginx config
    ```

6.  **Test Nginx Configuration and Restart:**
    ```bash
    sudo nginx -t
    sudo systemctl restart nginx
    ```

7.  **Access Your React App:**
    Open your browser and go to `http://20.6.88.232/elasticsearch-htx`.
    * **Important:** If using Nginx as a reverse proxy for Elasticsearch, update your React app's `fetch` calls to use `http://20.6.88.232/es/cv-transcriptions/_search` instead of `http://20.6.88.232:9200/cv-transcriptions/_search`.

#### Option B: Serving React Directly with `serve` (Simpler, but less scalable/robust for Production)

1.  **Build your React App Locally (using Vite and Yarn):** (Same as Option A)
    ```bash
    yarn install
    yarn build
    ```

2.  **Copy React Build to VM:**
    ```bash
    scp -r ./search-ui/dist chewhongjun@20.6.88.232:/home/chewhongjun/your-react-app-build
    ```

3.  **Install Node.js and `serve` on VM:**
    SSH into your VM:
    ```bash
    sudo apt update
    sudo apt install nodejs -y
    sudo apt install npm -y
    sudo npm install -g yarn
    sudo yarn global add serve
    ```

4.  **Stop Existing `serve` Process (if any):**
    If you have a `serve` process already running, you'll need to stop it.
    Find the process ID (PID):
    ```bash
    ps aux | grep serve
    ```
    Look for a line containing `serve -s . -l 5173` and note the PID (second column). Then kill it:
    ```bash
    kill <PID_OF_SERVE_PROCESS>
    ```

5.  **Run the React App:**
    Navigate to the build directory on your VM and start `serve`:
    ```bash
    cd /home/chewhongjun/your-react-app-build
    serve -s . -l 5173 # Ensure port 5173 is open in Azure NSG
    ```

6.  **Access Your React App:**
    Open your browser and go to `http://20.6.88.232:5173/elasticsearch-htx`.

### Step 5: Populate Elasticsearch with Data on VM

This section details how to transfer your data and the `cv-index.py` script to the VM and then run the script to populate your Elasticsearch index.

1.  **Prepare your Data and Script Locally:**
    Ensure your `cv-index.py` script and your `cv-valid-dev_transcribed.csv` file are in a known location on your local machine.
    * **Adjust `cv-index.py` path:** In your local `elastic-backend/cv-index.py` script, ensure `TRANSCRIPTION_CSV_PATH` is set to the correct relative path to your CSV file (e.g., `../cv-valid-dev/cv-valid-dev_transcribed.csv`).
    * **`ES_HOST` in `cv-index.py`:** Keep `ES_HOST = "localhost"` in `cv-index.py`. When run directly on the VM, `localhost` will correctly point to the Docker-exposed port 9200.

2.  **Copy Data and Script to VM:**
    From your local machine's terminal, navigate to the root of your project (where `elastic-backend` and `cv-valid-dev` might be):
    ```bash
    # Copy the Python script
    scp ./elastic-backend/cv-index.py chewhongjun@20.6.88.232:/home/chewhongjun/cv-index.py

    # Copy your CSV file (adjust local path as needed)
    scp ./cv-valid-dev/cv-valid-dev_transcribed.csv chewhongjun@20.6.88.232:/home/chewhongjun/cv-valid-dev_transcribed.csv
    ```
    You will be prompted for your password for each `scp` command.

3.  **Install Python Dependencies on VM:**
    SSH into your VM:
    ```bash
    ssh chewhongjun@20.6.88.232
    ```
    Once connected, install `pip` (if not already installed), `pandas`, and `elasticsearch`:
    ```bash
    sudo apt update
    sudo apt install python3-pip -y
    pip3 install pandas elasticsearch
    ```

4.  **Adjust Script Path on VM (if necessary):**
    If you copied the CSV to `/home/chewhongjun/cv-valid-dev_transcribed.csv` and the script to `/home/chewhongjun/cv-index.py`, you'll need to edit `cv-index.py` on the VM to reflect the correct absolute path.
    SSH into your VM and open the script:
    ```bash
    nano /home/chewhongjun/cv-index.py
    ```
    Change this line:
    `TRANSCRIPTION_CSV_PATH = "../cv-valid-dev/cv-valid-dev_transcribed.csv"`
    to:
    `TRANSCRIPTION_CSV_PATH = "/home/chewhongjun/cv-valid-dev_transcribed.csv"`
    Save and exit (`Ctrl+X`, `Y`, `Enter`).

5.  **Run the Python Script to Populate Data:**
    Ensure your Elasticsearch Docker containers are running (`docker ps` should show `es01` and `es02` as `Up`).
    Then, execute the Python script on your VM:
    ```bash
    python3 /home/chewhongjun/cv-index.py
    ```
    Monitor the output for success messages or any errors during indexing.

6.  **Verify Data in Elasticsearch:**
    After the script completes, you can check if data has been indexed by querying Elasticsearch from your local machine or VM:
    ```bash
    curl [http://20.6.88.232:9200/cv-transcriptions/_count?pretty](http://20.6.88.232:9200/cv-transcriptions/_count?pretty)
    ```
    The `count` field in the JSON response should show the number of documents indexed. You can also check Kibana at `http://20.6.88.232:5601` to explore the `cv-transcriptions` index.

### Step 6: (Optional) Configure Custom Domain and SSL (HTTPS)

For a production environment, you'll want to use a custom domain and secure your application with SSL (HTTPS). This typically involves Nginx and Certbot.

1.  **Point Your Domain:** In your domain registrar's DNS settings, create an `A` record that points your domain (e.g., `yourdomain.com`) to your Azure VM's `Public IP address`.
2.  **Install Certbot (on VM, if using Nginx):**
    ```bash
    sudo snap install core; sudo snap refresh core
    sudo snap install --classic certbot
    sudo ln -s /snap/bin/certbot /usr/bin/certbot
    ```
3.  **Obtain SSL Certificate (using Nginx plugin):**
    ```bash
    sudo certbot --nginx -d yourdomain.com -d [www.yourdomain.com](https://www.yourdomain.com)
    ```
    Follow the prompts. Certbot will automatically configure Nginx for HTTPS and set up automatic renewals.
4.  **Update Nginx Config (if not done by Certbot automatically or if using subdomains):**
    Ensure your Nginx `server_name` includes your domain, and that the `proxy_pass` URLs in your React app's `fetch` calls (and Elasticsearch CORS settings) are updated to use `https://yourdomain.com/es/` (or similar).

---

## 5. Important Considerations

* **Security:** For production deployments, enabling Elasticsearch security (X-Pack), securing Kibana, and restricting network access (NSG rules) are crucial. This guide assumes a development-like setup with security disabled for simplicity.
* **Data Persistence:** Ensure your Elasticsearch data volumes (`esdata01`, `esdata02`) are correctly mapped to persistent storage on the VM (e.g., Azure Managed Disks) to prevent data loss if containers are removed or the VM is restarted.
* **Monitoring & Logging:** Set up monitoring for your VM, Docker containers, Elasticsearch, and Kibana to track performance and troubleshoot issues.
* **Scalability:** For high-traffic or critical applications, consider Azure Kubernetes Service (AKS) or Azure Container Apps for more robust container orchestration and scalability.
* **Environment Variables:** For sensitive information (API keys, passwords), use environment variables in Docker Compose or Azure Key Vault, rather than hardcoding them.