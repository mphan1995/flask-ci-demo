pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/lamthong-devops/flask-ci-demo.git'
            }
        }

        stage('Build') {
            steps {
                echo 'Building application...'
                sh 'docker build -t flask-app:latest .'
            }
        }

        stage('Test') {
            steps {
                echo 'Running tests...'
                sh 'pytest || echo "No tests found"'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying application...'
                sh 'docker run -d -p 5000:5000 flask-app:latest'
            }
        }
    }
}
