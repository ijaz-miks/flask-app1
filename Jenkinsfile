pipeline {
    agent any

    environment {
        APP_NAME = "flask-app1" 
        DOCKER_IMAGE = "${env.APP_NAME}:${BUILD_NUMBER}"
        ECR_REPO = "public.ecr.aws/o0y6x7h1/sampleapp" // Your public ECR repo
        AWS_REGION = "us-east-1" // Your AWS region
    }

    stages {
        stage('Clone') {
            steps {
                git branch: 'master', url: 'git@github.com:ijaz-miks/flask-app1.git'
            }
        }

        stage('Build and Test') {
            steps {
                script {
                    // Build the Docker image
                    sh "docker build -t $DOCKER_IMAGE ."

                    // Run tests inside the container
                    def testExitCode = sh(script: "docker run $DOCKER_IMAGE python -m unittest test_app.py", returnStatus: true)
                    if (testExitCode != 0) {
                        error "Unit tests failed!"
                    }
                }
            }
        }

        stage('Push to ECR') {
            steps {
                script {
                    // Get the ECR authorization token
                    sh "aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/o0y6x7h1"

                    // Construct the ECR image tag
                    def ecrImageTag = "${ECR_REPO}/${APP_NAME}:${BUILD_NUMBER}"

                    // Tag the image for ECR
                    sh "docker tag ${DOCKER_IMAGE} ${ecrImageTag}"

                    // Push the image to ECR
                    sh "docker push ${ecrImageTag}"
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                script {
                    // Update the image tag in the deployment manifest
                    sh "sed -i 's#${ECR_REPO}/${APP_NAME}:.*#${ECR_REPO}/${APP_NAME}:${BUILD_NUMBER}#' kubernetes/deployment.yaml"

                    // Apply the Kubernetes manifests
                    sh "kubectl apply -f kubernetes/deployment.yaml --kubeconfig ${KUBE_CONFIG_PATH}"
                    sh "kubectl apply -f kubernetes/service.yaml --kubeconfig ${KUBE_CONFIG_PATH}"

                    // Wait for the deployment to complete
                    sh "kubectl rollout status deployment/${APP_NAME} --kubeconfig ${KUBE_CONFIG_PATH}"
                }
            }
        }
    }
}