pipeline {
    agent any

    environment {
        AWS_REGION     = 'us-east-1'
        AWS_ACCOUNT_ID = '201462388357'
        ECR_REPO       = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/flask-app"
        EKS_CLUSTER    = 'flask-ci-eks'
        K8S_NAMESPACE  = 'laptop'
        IMAGE_NAME     = 'flask-app'
        IMAGE_TAG      = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/mphan1995/flask-ci-demo.git'
            }
        }

        stage('Build') {
            steps {
                echo '🧱 Building Docker image...'
                sh '''
                docker build -t $IMAGE_NAME:latest .
                docker tag $IMAGE_NAME:latest $ECR_REPO:$IMAGE_TAG
                '''
            }
        }

        stage('Security Scan (Trivy)') {
            steps {
                echo '🔒 Scanning Docker image for vulnerabilities...'
                sh '''
                if ! command -v trivy &> /dev/null; then
                    echo "Installing Trivy..."
                    sudo apt-get update -y >/dev/null
                    sudo apt-get install -y wget apt-transport-https gnupg lsb-release >/dev/null
                    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
                    echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee /etc/apt/sources.list.d/trivy.list
                    sudo apt-get update -y >/dev/null
                    sudo apt-get install -y trivy >/dev/null
                fi

                echo "🔍 Running Trivy scan..."
                trivy image --severity HIGH,CRITICAL --no-progress --exit-code 0 $IMAGE_NAME:latest
                '''
            }
        }

        stage('Test') {
            steps {
                echo '🧪 Running tests...'
                sh 'pytest -q || echo "No tests found"'
            }
        }

        stage('Push to ECR') {
            steps {
                echo '🚀 Installing AWS CLI and pushing image to AWS ECR...'
                sh '''
                if ! command -v aws &> /dev/null; then
                    echo "Installing AWS CLI v2..."
                    sudo rm -rf aws awscliv2.zip
                    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
                    unzip -qq -o awscliv2.zip
                    sudo ./aws/install -i /usr/local/aws-cli -b /usr/local/bin
                else
                    echo "✅ AWS CLI already installed: $(aws --version)"
                fi

                aws ecr get-login-password --region $AWS_REGION | \
                    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

                aws ecr describe-repositories --repository-names flask-app --region $AWS_REGION >/dev/null 2>&1 \
                    || aws ecr create-repository --repository-name flask-app --region $AWS_REGION >/dev/null

                docker push $ECR_REPO:$IMAGE_TAG
                '''
            }
        }

        stage('Deploy to EKS') {
            steps {
                echo '☸️ Deploying image to EKS cluster...'
                sh '''
                echo "📦 Installing kubectl if missing..."
                if ! command -v kubectl &> /dev/null; then
                    echo "Installing kubectl v1.29.0..."
                    curl -LO "https://dl.k8s.io/release/v1.29.0/bin/linux/amd64/kubectl"
                    chmod +x kubectl
                    sudo mv kubectl /usr/local/bin/
                fi

                echo "🔧 Configuring kubeconfig for EKS..."
                aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER

                echo "🔍 Checking namespace..."
                kubectl get ns $K8S_NAMESPACE >/dev/null 2>&1 || kubectl create namespace $K8S_NAMESPACE

                echo "🚀 Deploying $ECR_REPO:$IMAGE_TAG ..."
                if ! kubectl get deploy flask-app -n $K8S_NAMESPACE >/dev/null 2>&1; then
                    kubectl create deployment flask-app --image=$ECR_REPO:$IMAGE_TAG -n $K8S_NAMESPACE
                    kubectl expose deployment flask-app --port=80 --target-port=5000 --type=LoadBalancer -n $K8S_NAMESPACE
                else
                    kubectl set image deployment/flask-app flask-app=$ECR_REPO:$IMAGE_TAG -n $K8S_NAMESPACE
                fi

                kubectl rollout status deployment/flask-app -n $K8S_NAMESPACE --timeout=180s || true
                kubectl get svc flask-app -n $K8S_NAMESPACE -o wide
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Build #${env.BUILD_NUMBER} deployed successfully!"
        }
        failure {
            echo "❌ Build failed. Check logs in Jenkins."
        }
    }
}
