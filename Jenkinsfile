pipeline {
    agent any

    environment {

        APP_NAME = "flask-app1"
        INVENTORY_APP_NAME = "inventory-app"
        USER_APP_NAME = "user-app"

        APP_DOCKER_IMAGE = "${env.APP_NAME}:${BUILD_NUMBER}"
        INVENTORY_DOCKER_IMAGE = "${env.INVENTORY_APP_NAME}:${BUILD_NUMBER}"
        USER_DOCKER_IMAGE = "${env.USER_APP_NAME}:${BUILD_NUMBER}"

        ECR_REPO = "public.ecr.aws/o0y6x7h1/sampleapp" // Your public ECR repo
        AWS_REGION = "us-east-1" // Your AWS region
        KUBE_CONFIG_PATH = "${HOME}/.kube/config"
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
                    sh "docker build -t sample-app/$APP_DOCKER_IMAGE sample-app/."
                    sh "docker build -t sample-app/$INVENTORY_DOCKER_IMAGE inventory-service/."
                    sh "docker build -t sample-app/$USER_DOCKER_IMAGE user-service/."

                    // Run tests inside the container
                    def testExitCode = sh(script: "docker run sample-app/$DOCKER_IMAGE python -m unittest test_app.py", returnStatus: true)
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
                    def ecrImageTagApp = "${ECR_REPO}/${APP_NAME}:${BUILD_NUMBER}"
                    def ecrImageTagInventory = "${ECR_REPO}/${INVENTORY_APP_NAME}:${BUILD_NUMBER}"
                    def ecrImageTagUser = "${ECR_REPO}/${USER_APP_NAME}:${BUILD_NUMBER}"

                    // Tag the image for ECR
                    sh "docker tag ${APP_DOCKER_IMAGE} ${ecrImageTagApp}"
                    sh "docker tag ${INVENTORY_DOCKER_IMAGE} ${ecrImageTagInventory}"
                    sh "docker tag ${USER_DOCKER_IMAGE} ${ecrImageTagUser}"


                    // Push the image to ECR
                    sh "docker push ${ecrImageTagApp}"
                    sh "docker push ${ecrImageTagInventory}"
                    sh "docker push ${ecrImageTagUser}"

                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                script {
                    // Update the image tag in the deployment manifest
                    sh "sed -i 's#${ECR_REPO}/${APP_NAME}:.*#${ECR_REPO}/${APP_NAME}:${BUILD_NUMBER}#' kubernetes/app-service-deployment.yaml"
                    sh "sed -i 's#${ECR_REPO}/${INVENTORY_APP_NAME}:.*#${ECR_REPO}/${INVENTORY_APP_NAME}:${BUILD_NUMBER}#' kubernetes/inventory-service-deployment.yaml"
                    sh "sed -i 's#${ECR_REPO}/${USER_APP_NAME}:.*#${ECR_REPO}/${USER_APP_NAME}:${BUILD_NUMBER}#' kubernetes/user-service-deployment.yaml"

                    // Apply the Kubernetes manifests
                    sh "kubectl apply -f kubernetes/app-service-deployment.yaml --kubeconfig ${KUBE_CONFIG_PATH}"
                    sh "kubectl apply -f kubernetes/inventory-service-deployment.yaml --kubeconfig ${KUBE_CONFIG_PATH}"
                    sh "kubectl apply -f kubernetes/user-service-deployment.yaml --kubeconfig ${KUBE_CONFIG_PATH}"
                    sh "kubectl apply -f kubernetes/ingress.yaml --kubeconfig ${KUBE_CONFIG_PATH}"

                    // Wait for the deployment to complete
                    sh "kubectl rollout status deployment/${APP_NAME} --kubeconfig ${KUBE_CONFIG_PATH} -n flask-app"
                    sh "kubectl rollout status deployment/${INVENTORY_APP_NAME} --kubeconfig ${KUBE_CONFIG_PATH} -n flask-app"
                    sh "kubectl rollout status deployment/${USER_APP_NAME} --kubeconfig ${KUBE_CONFIG_PATH} -n flask-app"

                }
            }
        }
    }
}