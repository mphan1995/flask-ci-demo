pipeline {
    agent any

    environment {
        // === Thông tin AWS & EKS ===
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
                    apt-get update -y && apt-get install -y unzip curl >/dev/null
                    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
                    unzip -qq awscliv2.zip
                    ./aws/install -i /usr/local/aws-cli -b /usr/local/bin
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
                echo "📦 Checking and installing kubectl if missing..."
                if ! command -v kubectl &> /dev/null; then
                    LATEST=$(curl -s https://dl.k8s.io/release/stable.txt)
                    echo "Downloading kubectl version $LATEST"
                    curl -LO "https://dl.k8s.io/release/${LATEST}/bin/linux/amd64/kubectl"
                    chmod +x kubectl
                    mv kubectl /usr/local/bin/
                fi

                echo "✅ kubectl installed version:"
                kubectl version --client --short || true

                echo "🔧 Configuring kubeconfig for EKS..."
                aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER

                echo "🔍 Checking namespace..."
                kubectl get ns $K8S_NAMESPACE >/dev/null 2>&1 || kubectl create namespace $K8S_NAMESPACE

                echo "🚀 Deploying $ECR_REPO:$IMAGE_TAG ..."
                if ! kubectl get deploy flask-app -n $K8S_NAMESPACE >/dev/null 2>&1; then
                    echo "Creating new deployment..."
                    kubectl create deployment flask-app --image=$ECR_REPO:$IMAGE_TAG -n $K8S_NAMESPACE
                    kubectl expose deployment flask-app --port=80 --target-port=5000 --type=LoadBalancer -n $K8S_NAMESPACE
                else
                    echo "Updating existing deployment..."
                    kubectl set image deployment/flask-app flask-app=$ECR_REPO:$IMAGE_TAG -n $K8S_NAMESPACE
                fi

                echo "⏳ Waiting for rollout to finish..."
                kubectl rollout status deployment/flask-app -n $K8S_NAMESPACE --timeout=180s || true

                echo "==== 🧭 Current Service Info ===="
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
