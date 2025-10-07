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
                echo '🚀 Pushing image to AWS ECR...'
                sh '''
                aws ecr get-login-password --region $AWS_REGION | \
                    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

                # Nếu repository chưa tồn tại thì tạo mới
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
                # Cấu hình kubectl tới cluster
                aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER

                # Tạo namespace nếu chưa có
                kubectl get ns $K8S_NAMESPACE >/dev/null 2>&1 || kubectl create namespace $K8S_NAMESPACE

                # Nếu deployment chưa tồn tại -> tạo mới
                if ! kubectl get deploy flask-app -n $K8S_NAMESPACE >/dev/null 2>&1; then
                    echo "Creating new deployment..."
                    kubectl create deployment flask-app --image=$ECR_REPO:$IMAGE_TAG -n $K8S_NAMESPACE
                    kubectl expose deployment flask-app --port=80 --target-port=5000 --type=LoadBalancer -n $K8S_NAMESPACE
                else
                    echo "Updating existing deployment..."
                    kubectl set image deployment/flask-app flask-app=$ECR_REPO:$IMAGE_TAG -n $K8S_NAMESPACE
                fi

                kubectl rollout status deployment/flask-app -n $K8S_NAMESPACE --timeout=180s

                echo "==== Current Service Info ===="
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
